#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/5 上午8:49
@Author : zsting29@gmail.com
@File   : document_service.py
"""
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from redis import Redis
from sqlalchemy import desc, func, asc

from internal.entity.cache_entity import LOCK_DOCUMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME
from internal.entity.dataset_entity import ProcessType, SegmentStatus, DocumentStatus
from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSION
from internal.exception import ForbiddenException, FailException, NotFoundException
from internal.lib.helper import datetime_to_timestamp
from internal.model import Document, Dataset, UploadFile, ProcessRule, Segment, Account
from internal.schema.document_schema import GetDocumentsWithPageReq
from internal.task.document_task import build_documents, update_document_enabled, delete_document
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class DocumentService(BaseService):
    """文檔服務"""
    db: SQLAlchemy
    redis_client: Redis

    def create_documents(
            self,
            dataset_id: UUID,
            upload_file_ids: list[UUID],
            process_type: str = ProcessType.AUTOMATIC,
            rule: dict = None,
            account: Account = None,
    ) -> tuple[list[Document], str]:
        """根據傳遞的資訊創建文件列表並調用異步任務"""
        # 1.檢測知識庫權限
        dataset = self.get(Dataset, dataset_id)
        print(dataset is None)
        print(dataset.account_id != account.id)
        if dataset is None or dataset.account_id != account.id:
            raise ForbiddenException("當前用戶無該知識庫權限或知識庫不存在")

        # 2.提取文件並校驗文件權限與文件擴展
        upload_files = self.db.session.query(UploadFile).filter(
            UploadFile.account_id == account.id,
            UploadFile.id.in_(upload_file_ids),
        ).all()

        upload_files = [
            upload_file for upload_file in upload_files
            if upload_file.extension.lower() in ALLOWED_DOCUMENT_EXTENSION
        ]

        if len(upload_files) == 0:
            logging.warning(
                "上傳文件列表未解析到合法文件, "
                "account_id: %(account_id)s, "
                "dataset_id: %(dataset_id)s, "
                "upload_file_ids: %(upload_file_ids)s",
                {"account_id": account.id, "dataset_id": dataset_id, "update_file_ids": repr(upload_file_ids)},
            )
            raise FailException("暫未解析到合法文件，請重新上傳")

        # 3.創建批次與處理規則並記錄到資料庫中
        batch = time.strftime("%Y%m%d%H%M%S") + str(random.randint(100000, 999999))
        process_rule = self.create(
            ProcessRule,
            account_id=account.id,
            dataset_id=dataset_id,
            mode=process_type,
            rule=rule,
        )

        # 4.獲取當前知識庫的最新檔案位置
        position = self.get_latest_document_position(dataset_id)

        # 5.循環遍歷所有合法的上傳文件列表並記錄
        documents = []
        for upload_file in upload_files:
            position += 1
            document = self.create(
                Document,
                account_id=account.id,
                dataset_id=dataset_id,
                upload_file_id=upload_file.id,
                process_rule_id=process_rule.id,
                batch=batch,
                name=upload_file.name,
                position=position,
            )
            documents.append(document)

        # 6.調用非同步任務，完成後續操作
        build_documents.delay([document.id for document in documents])

        # 7.返回文件列表與處理批次
        return documents, batch

    def get_documents_status(self, dataset_id: UUID, batch: str, account: Account) -> list[dict]:
        """根據傳遞的知識庫id+處理批次獲取文件列表的狀態"""
        # 1.檢測知識庫權限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise ForbiddenException("當前用戶無該知識庫權限或知識庫不存在")

        # 2.查詢當前知識庫下該批次的文件列表
        documents = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id,
            Document.batch == batch,
        ).order_by(asc("position")).all()
        if documents is None or len(documents) == 0:
            raise NotFoundException("該處理批次未發現文件，請核實後重試")

        # 3.循環遍歷文件列表提取文件的狀態資訊
        documents_status = []
        for document in documents:
            # 4.查詢每個文件的總片段數和已構建完成的片段數
            segment_count = self.db.session.query(func.count(Segment.id)).filter(
                Segment.document_id == document.id,
            ).scalar()
            completed_segment_count = self.db.session.query(func.count(Segment.id)).filter(
                Segment.document_id == document.id,
                Segment.status == SegmentStatus.COMPLETED,
            ).scalar()

            upload_file = document.upload_file
            documents_status.append({
                "id": document.id,
                "name": document.name,
                "size": upload_file.size,
                "extension": upload_file.extension,
                "mime_type": upload_file.mime_type,
                "position": document.position,
                "segment_count": segment_count,
                "completed_segment_count": completed_segment_count,
                "error": document.error,
                "status": document.status,
                "processing_started_at": datetime_to_timestamp(document.processing_started_at),
                "parsing_completed_at": datetime_to_timestamp(document.parsing_completed_at),
                "splitting_completed_at": datetime_to_timestamp(document.splitting_completed_at),
                "indexing_completed_at": datetime_to_timestamp(document.indexing_completed_at),
                "completed_at": datetime_to_timestamp(document.completed_at),
                "stopped_at": datetime_to_timestamp(document.stopped_at),
                "created_at": datetime_to_timestamp(document.created_at),
            })

        return documents_status

    def get_document(self, dataset_id: UUID, document_id: UUID, account: Account) -> Document:
        """根據傳遞的知識庫id+文件id獲取文件記錄資訊"""
        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("文件不存在，請核實後重試")
        if document.dataset_id != dataset_id or document.account_id != account.id:
            raise ForbiddenException("當前用戶獲取該文件，請核實後重試")

        return document

    def update_document(self, dataset_id: UUID, document_id: UUID, account: Account, **kwargs) -> Document:
        """根據傳遞的知識庫id+文件id，更新文件資訊"""
        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("文件不存在，請核實後重試")
        if document.dataset_id != dataset_id or document.account_id != account.id:
            raise ForbiddenException("當前用戶無權限修改該文件，請核實後重試")

        return self.update(document, **kwargs)

    def get_documents_with_page(
            self,
            dataset_id: UUID,
            req: GetDocumentsWithPageReq,
            account: Account
    ) -> tuple[list[Document], Paginator]:
        """根據傳遞的知識庫id+請求數據獲取文件分頁列表數據"""
        # 1.獲取知識庫並校驗權限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("該知識庫不存在，或無權限")

        # 2.構建分頁查詢器
        paginator = Paginator(db=self.db, req=req)

        # 3.構建篩選器
        filters = [
            Document.account_id == account.id,
            Document.dataset_id == dataset_id,
        ]
        if req.search_word.data:
            filters.append(Document.name.ilike(f"%{req.search_word.data}%"))

        # 4.執行分頁並獲取數據
        documents = paginator.paginate(
            self.db.session.query(Document).filter(*filters).order_by(desc("created_at"))
        )

        return documents, paginator

    def update_document_enabled(
            self,
            dataset_id: UUID,
            document_id: UUID,
            enabled: bool,
            account: Account,
    ) -> Document:
        """
        根據傳遞的知識庫id+文件id，更新文件的啟用狀態，
        同時會非同步更新weaviate向量資料庫中的數據
        """
        # 1.獲取文件並校驗權限
        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("該文件不存在，請核實後重試")
        if document.dataset_id != dataset_id or document.account_id != account.id:
            raise ForbiddenException("當前用戶無權限修改該知識庫下的文件，請核實後重試")

        # 2.判斷文件是否處於可以修改的狀態，只有構建完成才可以修改enabled
        if document.status != DocumentStatus.COMPLETED:
            raise ForbiddenException("當前文件處於不可修改狀態，請稍後重試")

        # 3.判斷修改的啟用狀態是否正確，需與當前的狀態相反
        if document.enabled == enabled:
            raise FailException(f"文件狀態修改錯誤，當前已是{'啟用' if enabled else '禁用'}狀態")

        # 4.獲取更新文件啟用狀態的快取鍵並檢測是否上鎖
        cache_key = LOCK_DOCUMENT_UPDATE_ENABLED.format(document_id=document.id)
        cache_result = self.redis_client.get(cache_key)
        if cache_result is not None:
            raise FailException("當前文件正在修改啟用狀態，請稍後再次嘗試")

        # 5.修改文件的啟用狀態並設置快取鍵，快取時間為600s
        self.update(
            document,
            enabled=enabled,
            disabled_at=None if enabled else datetime.now(),
        )
        self.redis_client.setex(cache_key, LOCK_EXPIRE_TIME, 1)

        # 6.啟用非同步任務完成後續操作
        update_document_enabled.delay(document.id)

        return document

    def delete_document(self, dataset_id: UUID, document_id: UUID, account: Account) -> Document:
        """根據傳遞的知識庫id+文件id刪除文件資訊，涵蓋：文件片段刪除、關鍵字表更新、weaviate向量資料庫記錄刪除"""
        # 1.獲取文件並校驗權限
        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("該文件不存在，請核實後重試")
        if document.dataset_id != dataset_id or document.account_id != account.id:
            raise ForbiddenException("當前用戶無權限刪除該知識庫下的文件，請核實後重試")

        # 2.判斷文件是否處於可刪除狀態，只有構建完成/出錯的時候才可以刪除，其他情況需要等待構建完成
        if document.status not in [DocumentStatus.COMPLETED, DocumentStatus.ERROR]:
            raise FailException("當前文件處於不可刪除狀態，請稍後重試")

        # 3.刪除postgres中的文件基礎資訊
        self.delete(document)

        # 4.調用非同步任務執行後續操作，涵蓋：關鍵字表更新、片段數據刪除、weaviate記錄刪除等
        delete_document.delay(dataset_id, document_id)

        return document

    def get_latest_document_position(self, dataset_id: UUID) -> int:
        """根據傳遞的知識庫id獲取最新檔案位置"""
        document = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id,
        ).order_by(desc("position")).first()
        return document.position if document else 0
