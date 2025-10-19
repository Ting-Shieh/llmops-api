#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/10 下午11:12
@Author : zsting29@gmail.com
@File   : segment_service.py
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from injector import inject
from langchain_core.documents import Document as LCDocument
from redis import Redis
from sqlalchemy import func, asc

from internal.entity.cache_entity import LOCK_SEGMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME
from internal.entity.dataset_entity import DocumentStatus, SegmentStatus
from internal.exception import (
    ValidateErrorException,
    NotFoundException,
    FailException
)
from internal.lib.helper import generate_text_hash
from internal.model import Segment, Document, Account
from internal.schema.segment_schema import (
    CreateSegmentReq,
    GetSegmentsWithPageReq, UpdateSegmentReq
)
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .embeddings_service import EmbeddingsService
from .jieba_service import JiebaService
from .keyword_table_service import KeywordTableService
from .vector_database_service import VectorDatabaseService


@inject
@dataclass
class SegmentService(BaseService):
    """片段服務"""
    db: SQLAlchemy
    redis_client: Redis
    jieba_service: JiebaService
    embeddings_service: EmbeddingsService
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService

    def create_segment(
            self,
            dataset_id: UUID,
            document_id: UUID,
            req: CreateSegmentReq,
            account: Account,
    ) -> Segment:
        """根據傳遞的資訊新增文件片段資訊"""
        # 1.校驗上傳內容的token長度總數，不能超過1000
        token_count = self.embeddings_service.calculate_token_count(req.content.data)
        if token_count > 1000:
            raise ValidateErrorException("片段內容的長度不能超過1000 token")

        # 2.獲取文件資訊並校驗
        document = self.get(Document, document_id)
        if (
                document is None
                or document.account_id != account.id
                or document.dataset_id != dataset_id
        ):
            raise NotFoundException("該知識庫文件不存在，或無權限新增，請核實後重試")

        # 3.判斷文件的狀態是否可以新增片段數據，只有completed才可以新增
        if document.status != DocumentStatus.COMPLETED:
            raise FailException("當前文件不可新增片段，請稍後嘗試")

        # 4.提取文件片段的最大位置
        position = self.db.session.query(func.coalesce(func.max(Segment.position), 0)).filter(
            Segment.document_id == document_id,
        ).scalar()

        # 5.檢測是否傳遞了keywords，如果沒有傳遞的話，調用jieba服務生成關鍵字
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        # 6.往postgres資料庫中新增記錄
        segment = None
        try:
            # 7.位置+1並且新增segment記錄
            position += 1
            segment = self.create(
                Segment,
                account_id=account.id,
                dataset_id=dataset_id,
                document_id=document_id,
                node_id=uuid4(),
                position=position,
                content=req.content.data,
                character_count=len(req.content.data),
                token_count=token_count,
                keywords=req.keywords.data,
                hash=generate_text_hash(req.content.data),
                enabled=True,
                processing_started_at=datetime.now(),
                indexing_completed_at=datetime.now(),
                completed_at=datetime.now(),
                status=SegmentStatus.COMPLETED,
            )

            # 8.往向量資料庫中新增數據
            self.vector_database_service.vector_store.add_documents(
                [LCDocument(
                    page_content=req.content.data,
                    metadata={
                        "account_id": str(document.account_id),
                        "dataset_id": str(document.dataset_id),
                        "document_id": str(document.id),
                        "segment_id": str(segment.id),
                        "node_id": str(segment.node_id),
                        "document_enabled": document.enabled,
                        "segment_enabled": True,
                    }
                )],
                ids=[str(segment.node_id)],
            )

            # 9.重新計算片段的字元總數以及token總數
            document_character_count, document_token_count = self.db.session.query(
                func.coalesce(func.sum(Segment.character_count), 0),
                func.coalesce(func.sum(Segment.token_count), 0)
            ).filter(Segment.document_id == document.id).first()

            # 10.更新文件的對應資訊
            self.update(
                document,
                character_count=document_character_count,
                token_count=document_token_count,
            )

            # 11.更新關鍵字表資訊
            if document.enabled is True:
                self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment.id])

        except Exception as e:
            logging.exception(
                "構建文件片段索引發生異常, 錯誤資訊: %(error)s",
                {"error": e},
            )
            if segment:
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
            raise FailException("新增文件片段失敗，請稍後嘗試")

    def get_segments_with_page(
            self,
            dataset_id: UUID,
            document_id: UUID,
            req: GetSegmentsWithPageReq,
            account: Account
    ) -> tuple[list[Segment], Paginator]:
        """根據傳遞的資訊獲取片段列表分頁數據"""

        # 1.獲取文件並校驗權限
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or document.account_id != account.id:
            raise NotFoundException("該知識庫文件不存在，或無權限查看，請核實後重試")

        # 2.構建分頁查詢器
        paginator = Paginator(db=self.db, req=req)

        # 3.構建篩選器
        filters = [Segment.document_id == document_id]
        if req.search_word.data:
            filters.append(Segment.content.ilike(f"%{req.search_word.data}%"))

        # 4.執行分頁並獲取數據
        segments = paginator.paginate(
            self.db.session.query(Segment).filter(*filters).order_by(asc("position"))
        )

        return segments, paginator

    def get_segment(
            self,
            dataset_id: UUID,
            document_id: UUID,
            segment_id: UUID,
            account: Account
    ) -> Segment:
        """根據傳遞的資訊獲取片段詳情資訊"""
        # 1.獲取片段資訊並校驗權限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("該文件片段不存在，或無權限查看，請核實後重試")

        return segment

    def update_segment_enabled(
            self,
            dataset_id: UUID,
            document_id: UUID,
            segment_id: UUID,
            enabled: bool,
            account: Account
    ) -> Segment:
        """根據傳遞的資訊更新文件片段的啟用狀態資訊"""

        # 1.獲取片段資訊並校驗權限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("該文件片段不存在，或無權限修改，請核實後重試")

        # 2.判斷文件片段是否處於可啟用/禁用的環境
        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("當前片段不可修改狀態，請稍後嘗試")

        # 3.判斷更新的片段啟用狀態和資料庫的數據是否一致，如果是則拋出錯誤
        if enabled == segment.enabled:
            raise FailException(f"片段狀態修改錯誤，當前已是{'啟用' if enabled else '禁用'}")

        # 4.獲取更新片段啟用狀態鎖並上鎖檢測
        cache_key = LOCK_SEGMENT_UPDATE_ENABLED.format(segment_id=segment_id)
        cache_result = self.redis_client.get(cache_key)
        if cache_result is not None:
            raise FailException("當前文件片段正在修改狀態，請稍後嘗試")

        # 5.上鎖並更新對應的數據，涵蓋postgres記錄、weaviate、關鍵字表
        with self.redis_client.lock(cache_key, LOCK_EXPIRE_TIME):
            try:
                # 6.修改postgres資料庫裡的文件片段狀態
                self.update(
                    segment,
                    enabled=enabled,
                    disabled_at=None if enabled else datetime.now()
                )

                # 7.更新關鍵字表的對應資訊，有可能新增，也有可能刪除
                document = segment.document
                if enabled is True and document.enabled is True:
                    self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment_id])
                else:
                    self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])

                # 8.同步處理weaviate向量資料庫裡的數據
                self.vector_database_service.collection.data.update(
                    uuid=segment.node_id,
                    properties={"segment_enabled": enabled}
                )
            except Exception as e:
                logging.exception(
                    "更改文件片段啟用狀態出現異常, segment_id: %(segment_id)s, 錯誤資訊: %(error)s",
                    {"segment_id": segment_id, "error": e},
                )
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
                raise FailException("更新文件片段啟用狀態失敗，請稍後重試")

    def delete_segment(
            self,
            dataset_id: UUID,
            document_id: UUID,
            segment_id: UUID,
            account: Account
    ) -> Segment:
        """根據傳遞的資訊刪除指定的文件片段資訊，該服務是同步方法"""
        # 1.獲取片段資訊並校驗權限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("該文件片段不存在，或無權限修改，請核實後重試")

        # 2.判斷文件是否處於可以刪除的狀態，只有COMPLETED/ERROR才可以刪除
        if segment.status not in [SegmentStatus.COMPLETED, SegmentStatus.ERROR]:
            raise FailException("當前文件片段處於不可刪除狀態，請稍後嘗試")

        # 3.刪除文件片段並獲取該片段的文件資訊
        document = segment.document
        self.delete(segment)

        # 4.同步刪除關鍵字表中屬於該片段的關鍵字
        self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])

        # 5.同步刪除向量資料庫儲存的紀錄
        try:
            self.vector_database_service.collection.data.delete_by_id(str(segment.node_id))
        except Exception as e:
            logging.exception(
                "刪除文件片段記錄失敗, segment_id: %(segment_id)s, 錯誤資訊: %(error)s",
                {"segment_id": segment_id, "error": e},
            )

        # 6.更新文件資訊，涵蓋字元總數、token總次數
        document_character_count, document_token_count = self.db.session.query(
            func.coalesce(func.sum(Segment.character_count), 0),
            func.coalesce(func.sum(Segment.token_count), 0)
        ).filter(Segment.document_id == document.id).first()
        self.update(
            document,
            character_count=document_character_count,
            token_count=document_token_count,
        )

        return segment

    def update_segment(
            self,
            dataset_id: UUID,
            document_id: UUID,
            segment_id: UUID,
            req: UpdateSegmentReq,
            account: Account
    ) -> Segment:
        """根據傳遞的資訊更新指定的文件片段資訊"""
        # 1.獲取片段資訊並校驗權限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("該文件片段不存在，或無權限修改，請核實後重試")

        # 2.判斷文件片段是否處於可修改的環境
        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("當前片段不可修改狀態，請稍後嘗試")

        # 3.檢測是否傳遞了keywords，如果沒有傳遞的話，調用jieba服務生成關鍵字
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        # 4.計算新內容hash值，用於判斷是否需要更新向量資料庫以及文件詳情
        new_hash = generate_text_hash(req.content.data)
        required_update = segment.hash != new_hash

        try:
            # 5.更新segment表記錄
            self.update(
                segment,
                keywords=req.keywords.data,
                content=req.content.data,
                hash=new_hash,
                character_count=len(req.content.data),
                token_count=self.embeddings_service.calculate_token_count(req.content.data),
            )

            # 7.更新片段歸屬關鍵字資訊
            self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])
            self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment_id])

            # 8.檢測是否需要更新文件資訊以及向量資料庫
            if required_update:
                # 7.更新文件資訊，涵蓋字元總數、token總次數
                document = segment.document
                document_character_count, document_token_count = self.db.session.query(
                    func.coalesce(func.sum(Segment.character_count), 0),
                    func.coalesce(func.sum(Segment.token_count), 0)
                ).filter(Segment.document_id == document.id).first()
                self.update(
                    document,
                    character_count=document_character_count,
                    token_count=document_token_count,
                )

                # 9.更新向量資料庫對應記錄
                self.vector_database_service.collection.data.update(
                    uuid=str(segment.node_id),
                    properties={
                        "text": req.content.data,
                    },
                    vector=self.embeddings_service.embeddings.embed_query(req.content.data)
                )
        except Exception as e:
            logging.exception(
                "更新文件片段記錄失敗, segment_id: %(segment_id)s, 錯誤資訊: %(error)s",
                {"segment_id": segment_id, "error": e},
            )
            raise FailException("更新文件片段記錄失敗，請稍後嘗試")

        return segment
