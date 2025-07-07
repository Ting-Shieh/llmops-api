#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/5 上午8:49
@Author : zsting29@gmail.com
@File   : document_service.py
"""
import logging
from dataclasses import dataclass
from datetime import time
from random import random
from uuid import UUID

from injector import inject
from sqlalchemy import desc, func, asc

from internal.entity.dataset_entity import ProcessType, SegmentStatus
from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSION
from internal.exception import ForbiddenException, FailException, NotFoundException
from internal.lib.helper import datetime_to_timestamp
from internal.model import Document, Dataset, UploadFile, ProcessRule, Segment
from internal.service import BaseService
from internal.task.document_task import build_documents


@inject
@dataclass
class DocumentService(BaseService):
    """文檔服務"""

    def create_documents(
            self,
            dataset_id: UUID,
            upload_file_ids: list[UUID],
            process_type: str = ProcessType.AUTOMATIC,
            rule: dict = None,
    ) -> tuple[list[Document], str]:
        """根據傳遞的資訊創建文件列表並調用異步任務"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        # 1.檢測知識庫權限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account_id:
            raise ForbiddenException("當前用戶無該知識庫權限或知識庫不存在")

        # 2.提取文件並校驗文件權限與文件擴展
        upload_files = self.db.session.query(UploadFile).filter(
            UploadFile.account_id == account_id,
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
                {"account_id": account_id, "dataset_id": dataset_id, "update_file_ids": repr(upload_file_ids)},
            )
            raise FailException("暫未解析到合法文件，請重新上傳")

        # 3.創建批次與處理規則並記錄到資料庫中
        batch = time.strftime("%Y%m%d%H%M%S") + str(random.randint(100000, 999999))
        process_rule = self.create(
            ProcessRule,
            account_id=account_id,
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
                account_id=account_id,
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

    def get_latest_document_position(self, dataset_id: UUID) -> int:
        """根據傳遞的知識庫id獲取最新檔案位置"""
        document = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id,
        ).order_by(desc("position")).first()
        return document.position if document else 0

    def get_documents_status(self, dataset_id: UUID, batch: str) -> list[dict]:
        """根據傳遞的知識庫id+處理批次獲取文件列表的狀態"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"
        # 1.檢測知識庫權限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account_id:
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
