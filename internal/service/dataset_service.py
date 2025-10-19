#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/19 上午6:36
@Author : zsting29@gmail.com
@File   : dataset_service.py
"""
import logging
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.entity.dataset_entity import (
    DEFAULT_DATASET_DESCRIPTION_FORMATTER
)
from internal.exception import (
    ValidateErrorException,
    NotFoundException,
    FailException
)
from internal.lib.helper import datetime_to_timestamp
from internal.model import (
    Dataset,
    DatasetQuery,
    Segment,
    AppDatasetJoin, Account
)
from internal.schema.dataset_schema import (
    CreateDatasetReq,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
    HitReq
)
from internal.task.dataset_task import delete_dataset
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .retrieval_service import RetrievalService


@inject
@dataclass
class DatasetService(BaseService):
    """知識庫服務"""
    db: SQLAlchemy
    retrieval_service: RetrievalService

    def create_dataset(self, req: CreateDatasetReq, account: Account) -> Dataset:
        """創建知識庫"""
        # 1.檢測該帳號下是否存在同名知識庫
        dataset = self.db.session.query(Dataset).filter_by(
            account_id=account.id,
            name=req.name.data,
        ).one_or_none()
        if dataset:
            raise ValidateErrorException(f"該知識庫{req.name.data}已存在")

        # 2.檢測是否傳遞描述訊息，如果没有傳遞需要補上
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        # 3.創建知識庫紀錄並返回
        return self.create(
            Dataset,
            account_id=account.id,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data,
        )

    def get_dataset_queries(self, dataset_id: UUID, account: Account) -> list[DatasetQuery]:
        """根據傳遞的知識庫id獲取最近的10條查詢記錄"""
        # 1.獲取知識庫並校驗權限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("該知識庫不存在")

        # 2.調用知識庫查詢模型尋找最近的10條紀錄
        dataset_queries = self.db.session.query(DatasetQuery).filter(
            DatasetQuery.dataset_id == dataset_id,
        ).order_by(desc("created_at")).limit(10).all()

        return dataset_queries

    def get_dataset(self, dataset_id: UUID, account: Account) -> Dataset:
        """根據知識庫ID獲取詳情"""
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("該知識庫不存在")

        return dataset

    def update_dataset(self, dataset_id: UUID, req: UpdateDatasetReq, account: Account) -> Dataset:
        """根據知識庫ID更新知識庫詳情"""
        # 1.檢測該帳號下是否存在知識庫
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("該知識庫不存在")

        # 2.檢測修改後的知識庫名稱是否重名
        check_dataset = self.db.session.query(Dataset).filter(
            Dataset.account_id == account.id,
            Dataset.name == req.name.data,
            Dataset.id != dataset_id,
        ).one_or_none()

        if check_dataset:
            raise ValidateErrorException(f"該知識庫名稱{req.name.data}已存在,請修改")

        # 3.校驗描述訊息是否為空，如果没有傳遞需要補上
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        # 4.更新紀錄並返回
        self.update(
            dataset,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data,
        )

        return dataset

    def get_dataset_with_page(self, req: GetDatasetsWithPageReq, account: Account) -> tuple[list[Dataset], Paginator]:
        """獲取知識庫分頁＆搜尋列表數據"""
        # 1.構建分頁查詢器
        paginator = Paginator(db=self.db, req=req)

        # 2.構建篩選器
        filters = [Dataset.account_id == account.id]
        if req.search_word.data:
            filters.append(Dataset.name.ilike(f"%{req.search_word.data}%"))

        # 3.執行分頁並獲取數據
        datasets = paginator.paginate(
            self.db.session.query(Dataset).filter(*filters).order_by(desc("created_at"))
        )

        return datasets, paginator

    def hit(self, dataset_id: UUID, req: HitReq, account: Account) -> list[dict]:
        """根據傳遞的知識庫id+請求執行召回測試"""

        # 1.知識庫並校驗權限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("該知識庫不存在")

        # 2.調用檢索服務執行檢索
        lc_documents = self.retrieval_service.search_in_datasets(
            dataset_ids=[dataset_id],
            account_id=account.id,
            **req.data,
        )
        lc_document_dict = {
            str(lc_document.metadata["segment_id"]): lc_document for lc_document in lc_documents
        }

        # 3.根據檢索到的數據查詢對應的片段資訊
        segments = self.db.session.query(Segment).filter(
            Segment.id.in_([str(lc_document.metadata["segment_id"]) for lc_document in lc_documents])
        ).all()
        segment_dict = {str(segment.id): segment for segment in segments}

        # 4.排序片段數據
        sorted_segments = [
            segment_dict[str(lc_document.metadata["segment_id"])]
            for lc_document in lc_documents
            if str(lc_document.metadata["segment_id"]) in segment_dict
        ]

        # 5.組裝響應數據
        hit_result = []
        for segment in sorted_segments:
            document = segment.document
            upload_file = document.upload_file
            hit_result.append({
                "id": segment.id,
                "document": {
                    "id": document.id,
                    "name": document.name,
                    "extension": upload_file.extension,
                    "mime_type": upload_file.mime_type,
                },
                "dataset_id": segment.dataset_id,
                "score": lc_document_dict[str(segment.id)].metadata["score"],
                "position": segment.position,
                "content": segment.content,
                "keywords": segment.keywords,
                "character_count": segment.character_count,
                "token_count": segment.token_count,
                "hit_count": segment.hit_count,
                "enabled": segment.enabled,
                "disabled_at": datetime_to_timestamp(segment.disabled_at),
                "status": segment.status,
                "error": segment.error,
                "updated_at": datetime_to_timestamp(segment.updated_at),
                "created_at": datetime_to_timestamp(segment.created_at),
            })

        return hit_result

    def delete_dataset(self, dataset_id: UUID, account: Account) -> Dataset:
        """
        根據傳遞的知識庫id刪除知識庫資訊，
        涵蓋知識庫底下的所有文件、片段、關鍵字，以及向量資料庫裡儲存的數據
        """
        # 1.獲取知識庫並校驗權限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("該知識庫不存在")

        try:
            # 2.刪除知識庫基礎記錄以及知識庫和應用關聯的紀錄
            self.delete(dataset)
            with self.db.auto_commit():
                self.db.session.query(AppDatasetJoin).filter(
                    AppDatasetJoin.dataset_id == dataset_id,
                ).delete()

            # 3.調用非同步任務執行後續的操作
            delete_dataset.delay(dataset_id)
        except Exception as e:
            logging.exception(
                "刪除知識庫失敗, dataset_id: %(dataset_id)s, 錯誤資訊: %(error)s",
                {"dataset_id": dataset_id, "error": e},
            )
            raise FailException("刪除知識庫失敗，請稍後重試")
