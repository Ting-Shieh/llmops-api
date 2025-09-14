#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/5 下午8:00
@Author : zsting29@gmail.com
@File   : indexing_service.py
"""
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from langchain_core.documents import Document as LCDocument
from redis import Redis
from sqlalchemy import func
from weaviate.classes.query import Filter

from internal.core.file_extractor import FileExtractor
from internal.entity.cache_entity import LOCK_DOCUMENT_UPDATE_ENABLED
from internal.entity.dataset_entity import DocumentStatus, SegmentStatus
from internal.exception import NotFoundException
from internal.lib.helper import generate_text_hash
from internal.model import Document, Segment, DatasetQuery, KeywordTable
from internal.service.base_service import BaseService
from internal.service.embeddings_service import EmbeddingsService
from internal.service.jieba_service import JiebaService
from internal.service.keyword_table_service import KeywordTableService
from internal.service.process_rule_service import ProcessRuleService
from internal.service.vector_database_service import VectorDatabaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class IndexingService(BaseService):
    """勾引構建服務"""
    db: SQLAlchemy
    redis_client: Redis
    file_extractor: FileExtractor
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    vector_database_service: VectorDatabaseService
    process_rule_service: ProcessRuleService
    keyword_table_service: KeywordTableService

    def build_documents(self, document_ids: list[UUID]) -> None:
        """根據傳遞的文件id列表構建知識庫文件，涵蓋了載入、分割、索引構建、數據儲存等內容"""
        # 1.根據傳遞的文件id獲取所有文件
        documents = self.db.session.query(Document).filter(
            Document.id.in_(document_ids)
        ).all()

        # 2.執行循環遍歷所有文件完成對每個文件的構建
        for document in documents:
            try:
                # 3.更新當前狀態為解析中，並記錄開始處理的時間
                self.update(document, status=DocumentStatus.PARSING, processing_started_at=datetime.now())

                # 4.執行文件載入步驟，並更新文件的狀態與時間
                lc_documents = self._parsing(document)

                # 5.執行文件分割步驟，並更新文件狀態與時間，涵蓋了片段的資訊
                lc_segments = self._splitting(document, lc_documents)

                # 6.執行文件索引構建，涵蓋關鍵字提取、向量，並更新數據狀態
                self._indexing(document, lc_segments)

                # 7.儲存操作，涵蓋文件狀態更新，以及向量資料庫的儲存
                self._completed(document, lc_segments)

            except Exception as e:
                logging.exception("構建文件發生錯誤, 錯誤資訊: %(error)s", {"error": e})
                self.update(
                    document,
                    status=DocumentStatus.ERROR,
                    error=str(e),
                    stopped_at=datetime.now(),
                )

    def update_document_enabled(self, document_id: UUID) -> None:
        """根據傳遞的文件id更新文件狀態，同時修改weaviate向量資料庫中的紀錄勾引構建服務"""
        # 1.構建快取鍵
        cache_key = LOCK_DOCUMENT_UPDATE_ENABLED.format(document_id=document_id)

        # 2.根據傳遞的document_id獲取文件記錄
        document = self.get(Document, document_id)
        if document is None:
            logging.exception("當前文件不存在, 文件id: %(document_id)s", {"document_id": document_id})
            raise NotFoundException("當前文件不存在")

        # 3.查詢歸屬於當前文件的所有片段的節點id
        segments = self.db.session.query(Segment).with_entities(Segment.id, Segment.node_id, Segment.enabled).filter(
            Segment.document_id == document_id,
            Segment.status == SegmentStatus.COMPLETED,
        ).all()
        segment_ids = [id for id, _, _ in segments]
        node_ids = [node_id for _, node_id, _ in segments]
        try:
            # 4.執行循環遍歷所有node_ids並更新向量數據
            collection = self.vector_database_service.collection
            for node_id in node_ids:
                try:
                    collection.data.update(
                        uuid=node_id,
                        properties={
                            "document_enabled": document.enabled,
                        }
                    )
                except Exception as e:
                    with self.db.auto_commit():
                        self.db.session.query(Segment).filter(
                            Segment.node_id == node_id,
                        ).update({
                            "error": str(e),
                            "status": SegmentStatus.ERROR,
                            "enabled": False,
                            "disabled_at": datetime.now(),
                            "stopped_at": datetime.now(),
                        })

            # 5.更新關鍵字表對應的數據（enabled為false表示從關鍵字表中刪除數據，enabled為true表示在關鍵字表中新增數據）
            if document.enabled is True:
                # 6.從禁用改為啟用，需要新增關鍵字
                enabled_segment_ids = [id for id, _, enabled in segments if enabled is True]
                self.keyword_table_service.add_keyword_table_from_ids(document.dataset_id, enabled_segment_ids)
            else:
                # 7.從啟用改為禁用，需要剔除關鍵字
                self.keyword_table_service.delete_keyword_table_from_ids(document.dataset_id, segment_ids)
        except Exception as e:
            # 5.記錄日誌並將狀態修改回原來的狀態
            logging.exception(
                "修改向量資料庫文件啟用狀態失敗, document_id: %(document_id)s, 錯誤資訊: %(error)s",
                {"document_id": document_id, "error": e},
            )
            origin_enabled = not document.enabled
            self.update(
                document,
                enabled=origin_enabled,
                disabled_at=None if origin_enabled else datetime.now(),
            )
        finally:
            # 6.清空快取鍵表示非同步操作已經執行完成，無論失敗還是成功都全部清除
            self.redis_client.delete(cache_key)

    def delete_document(self, dataset_id: UUID, document_id: UUID) -> None:
        """根據傳遞的知識庫id+文件id刪除文件資訊"""
        # 1.尋找該文件下的所有片段id列表
        segment_ids = [
            str(id) for id, in self.db.session.query(Segment).with_entities(Segment.id).filter(
                Segment.document_id == document_id,
            ).all()
        ]

        # 2.調用向量資料庫刪除其關聯記錄
        collection = self.vector_database_service.collection
        collection.data.delete_many(
            where=Filter.by_property("document_id").equal(document_id),
        )

        # 3.刪除postgres關聯的segment記錄
        with self.db.auto_commit():
            self.db.session.query(Segment).filter(
                Segment.document_id == document_id,
            ).delete()

        # 4.刪除片段id對應的關鍵字記錄
        self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, segment_ids)

    def delete_dataset(self, dataset_id: UUID) -> None:
        """根據傳遞的知識庫id執行相應的刪除操作"""
        try:
            with self.db.auto_commit():
                # 1.刪除關聯的文件記錄
                self.db.session.query(Document).filter(
                    Document.dataset_id == dataset_id,
                ).delete()

                # 2.刪除關聯的片段記錄
                self.db.session.query(Segment).filter(
                    Segment.dataset_id == dataset_id,
                ).delete()

                # 3.刪除關聯的關鍵字表記錄
                self.db.session.query(KeywordTable).filter(
                    KeywordTable.dataset_id == dataset_id,
                ).delete()

                # 4.刪除知識庫查詢記錄
                self.db.session.query(DatasetQuery).filter(
                    DatasetQuery.dataset_id == dataset_id,
                ).delete()

            # 5.調用向量資料庫刪除知識庫的關聯記錄
            self.vector_database_service.collection.data.delete_many(
                where=Filter.by_property("dataset_id").equal(str(dataset_id))
            )
        except Exception as e:
            logging.exception(
                "非同步刪除知識庫關聯內容出錯, dataset_id: %(dataset_id)s, 錯誤資訊: %(error)s",
                {"dataset_id": dataset_id, "error": e},
            )

    def _parsing(self, document: Document) -> list[LCDocument]:
        """解析傳遞的文件為LangChain文件列表"""
        # 1.獲取upload_file並載入LangChain文件
        upload_file = document.upload_file
        lc_documents = self.file_extractor.load(upload_file, False, True)

        # 2.循環處理LangChain文件，並刪除多餘的空白字串
        for lc_document in lc_documents:
            lc_document.page_content = self._clean_extra_text(lc_document.page_content)

        # 3.更新文件狀態並記錄時間
        self.update(
            document,
            character_count=sum([len(lc_document.page_content) for lc_document in lc_documents]),
            status=DocumentStatus.SPLITTING,
            parsing_completed_at=datetime.now(),
        )

        return lc_documents

    def _splitting(self, document: Document, lc_documents: list[LCDocument]) -> list[LCDocument]:
        """根據傳遞的資訊進行文件分割，拆分成小塊片段"""
        try:
            # 1.根據process_rule獲取文本分割器
            process_rule = document.process_rule
            text_splitter = self.process_rule_service.get_text_splitter_by_process_rule(
                process_rule,
                self.embeddings_service.calculate_token_count,
            )

            # 2.按照process_rule規則清除多餘的字串
            for lc_document in lc_documents:
                lc_document.page_content = self.process_rule_service.clean_text_by_process_rule(
                    lc_document.page_content,
                    process_rule,
                )

            # 3.分割文件列表為片段列表
            lc_segments = text_splitter.split_documents(lc_documents)

            # 4.獲取對應文件下得到最大片段位置
            position = self.db.session.query(func.coalesce(func.max(Segment.position), 0)).filter(
                Segment.document_id == document.id,
            ).scalar()

            # 5.循環處理片段數據並添加元數據，同時儲存到postgres資料庫中
            segments = []
            for lc_segment in lc_segments:
                position += 1
                content = lc_segment.page_content
                segment = self.create(
                    Segment,
                    account_id=document.account_id,
                    dataset_id=document.dataset_id,
                    document_id=document.id,
                    node_id=uuid.uuid4(),
                    position=position,
                    content=content,
                    character_count=len(content),
                    token_count=self.embeddings_service.calculate_token_count(content),
                    hash=generate_text_hash(content),
                    status=SegmentStatus.WAITING,
                )
                lc_segment.metadata = {
                    "account_id": str(document.account_id),
                    "dataset_id": str(document.dataset_id),
                    "document_id": str(document.id),
                    "segment_id": str(segment.id),
                    "node_id": str(segment.node_id),
                    "document_enabled": False,
                    "segment_enabled": False,
                }
                segments.append(segment)

            # 6.更新文件的數據，涵蓋狀態、token數等內容
            self.update(
                document,
                token_count=sum([segment.token_count for segment in segments]),
                status=DocumentStatus.INDEXING,
                splitting_completed_at=datetime.now(),
            )

            return lc_segments
        except Exception as e:
            print("_splitting出現異常:", e)

    def _indexing(self, document: Document, lc_segments: list[LCDocument]) -> None:
        """根據傳遞的資訊構建索引，涵蓋關鍵字提取、詞表構建"""
        for lc_segment in lc_segments:
            # 1.提取每一個片段對應的關鍵字，關鍵字的數量最多不超過10個
            keywords = self.jieba_service.extract_keywords(lc_segment.page_content, 10)

            # 2.逐條更新文件片段的關鍵字
            self.db.session.query(Segment).filter(
                Segment.id == lc_segment.metadata["segment_id"]
            ).update({
                "keywords": keywords,
                "status": SegmentStatus.INDEXING,
                "indexing_completed_at": datetime.now(),
            })

            # 3.獲取當前知識庫的關鍵字表
            keyword_table_record = self.keyword_table_service.get_keyword_table_from_dataset_id(document.dataset_id)

            keyword_table = {
                field: set(value) for field, value in keyword_table_record.keyword_table.items()
            }

            # 4.循環將新關鍵字添加到關鍵字表中
            for keyword in keywords:
                if keyword not in keyword_table:
                    keyword_table[keyword] = set()
                keyword_table[keyword].add(lc_segment.metadata["segment_id"])

            # 5.更新關鍵字表
            self.update(
                keyword_table_record,
                keyword_table={field: list(value) for field, value in keyword_table.items()}
            )

        # 6.更新文件狀態
        self.update(
            document,
            indexing_completed_at=datetime.now(),
        )

    def _completed(self, document: Document, lc_segments: list[LCDocument]) -> None:
        """儲存文件片段到向量資料庫，並完成狀態更新"""
        # 1.循環遍歷片段列表數據，將文件狀態及片段狀態設置成True
        for lc_segment in lc_segments:
            lc_segment.metadata["document_enabled"] = True
            lc_segment.metadata["segment_enabled"] = True

        # 2.調用向量資料庫，每次儲存10條數據，避免一次傳遞過多的數據
        try:
            for i in range(0, len(lc_segments), 10):
                # 3.提取需要存儲的數據與ID
                chunks = lc_segments[i:i + 10]
                ids = [chunk.metadata["node_id"] for chunk in chunks]

                # 4.調用向量數據庫存儲對應的數據
                self.vector_database_service.vector_store.add_documents(chunks, ids=ids)

                # 5.更新關聯片段的狀況以及完成時間
                with self.db.auto_commit():
                    self.db.session.query(Segment).filter(
                        Segment.node_id.in_(ids)
                    ).update({
                        "status": SegmentStatus.COMPLETED,
                        "completed_at": datetime.now(),
                        "enabled": True,
                    })
        except Exception as e:
            logging.exception(
                "構建文件片段索引發生異常, 錯誤資訊: %(error)s",
                {"error": e},
            )
            with self.db.auto_commit():
                self.db.session.query(Segment).filter(
                    Segment.node_id.in_(ids)
                ).update({
                    "status": SegmentStatus.ERROR,
                    "completed_at": None,
                    "stopped_at": datetime.now(),
                    "enabled": False,
                    "error": str(e),
                })

        # 6.更新文件的狀態數據
        self.update(
            document,
            status=DocumentStatus.COMPLETED,
            completed_at=datetime.now(),
            enabled=True,
        )

    @classmethod
    def _clean_extra_text(cls, text: str) -> str:
        """清除過濾傳遞的多餘空白字串"""
        text = re.sub(r'<\|', '<', text)
        text = re.sub(r'\|>', '>', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]', '', text)
        text = re.sub('\uFFFE', '', text)  # 刪除零寬非標記字元
        return text
