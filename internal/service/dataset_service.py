#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/19 上午6:36
@Author : zsting29@gmail.com
@File   : dataset_service.py
"""
import uuid
from dataclasses import dataclass

from injector import inject
from sqlalchemy import desc

from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from internal.exception import ValidateErrorException, NotFoundException
from internal.model import Dataset
from internal.schema.dataset_schema import CreateDatasetReq, UpdateDatasetReq, GetDatasetsWithPageReq
from internal.service import BaseService
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DatasetService(BaseService):
    """知識庫服務"""
    db: SQLAlchemy

    def create_dataset(self, req: CreateDatasetReq) -> Dataset:
        """創建知識庫"""
        # 1.檢測該帳號下是否存在同名知識庫
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        dataset = self.db.session.query(Dataset).filter_by(
            account_id=account_id,
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
            account_id=account_id,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data,
        )

    def get_dataset(self, dataset_id: uuid.UUID) -> Dataset:
        """根據知識庫ID獲取詳情"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("該知識庫不存在")

        return dataset

    def update_dataset(self, dataset_id: uuid.UUID, req: UpdateDatasetReq) -> Dataset:
        """根據知識庫ID更新知識庫詳情"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"
        # 1.檢測該帳號下是否存在知識庫
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("該知識庫不存在")

        # 2.檢測修改後的知識庫名稱是否重名
        check_dataset = self.db.session.query(Dataset).filter(
            Dataset.account_id == account_id,
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

    def get_dataset_with_page(self, req: GetDatasetsWithPageReq) -> tuple[list[Dataset], Paginator]:
        """獲取知識庫分頁＆搜尋列表數據"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"
        # 1.構建分頁查詢器
        paginator = Paginator(db=self.db, req=req)

        # 2.構建篩選器
        filters = [Dataset.account_id == account_id]
        if req.search_word.data:
            filters.append(Dataset.name.ilike(f"%{req.search_word.data}%"))

        # 3.執行分頁並獲取數據
        datasets = paginator.paginate(
            self.db.session.query(Dataset).filter(*filters).order_by(desc("created_at"))
        )

        return datasets, paginator
