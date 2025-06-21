#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/17 上午7:45
@Author : zsting29@gmail.com
@File   : dataset_handler.py
"""
import uuid
from dataclasses import dataclass

from flask import request
from injector import inject

from internal.schema.dataset_schema import CreateDatasetReq, GetDatasetResp, UpdateDatasetReq, GetDatasetsWithPageReq, \
    GetDatasetsWithPageResp
from internal.service import DatasetService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class DatasetHandler:
    """知識庫控制器"""
    dataset_service: DatasetService

    def create_dataset(self):
        """創建知識庫"""
        # 1.提取請求的數據並校驗
        req = CreateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建知識庫
        self.dataset_service.create_dataset(req)

        return success_message(f"知識庫已經成功創建")

    def get_dataset(self, dataset_id: uuid.UUID):
        """根據知識庫ID獲取詳情"""
        dataset = self.dataset_service.get_dataset(dataset_id)
        resp = GetDatasetResp()
        return success_json(resp.dump(dataset))

    def update_dataset(self, dataset_id: uuid.UUID):
        """根據知識庫ID更新知識庫詳情"""
        # 1.提取請求的數據並校驗
        req = UpdateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建知識庫
        self.dataset_service.update_dataset(dataset_id, req)

        return success_message(f"知識庫已經成功更新")

    def get_dataset_with_page(self):
        """獲取知識庫分頁＆搜尋列表數據"""
        # 1.提取query數據並校驗
        req = GetDatasetsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        datasets, paginator = self.dataset_service.get_dataset_with_page(req)

        resp = GetDatasetsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))
