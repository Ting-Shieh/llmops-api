#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/17 上午7:45
@Author : zsting29@gmail.com
@File   : dataset_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required
from injector import inject

from internal.core.file_extractor import FileExtractor
from internal.model import UploadFile
from internal.schema.dataset_schema import (
    CreateDatasetReq,
    GetDatasetResp,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
    GetDatasetsWithPageResp,
    HitReq, GetDatasetQueriesResp
)
from internal.service import DatasetService, EmbeddingsService, JiebaService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DatasetHandler:
    """知識庫控制器"""
    dataset_service: DatasetService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    file_extractor: FileExtractor
    db: SQLAlchemy

    def embeddings_query(self):
        upload_file = self.db.session.query(UploadFile).get("772ca820-a1ce-4d99-b7f2-3443fcca2dc3")
        content = self.file_extractor.load(upload_file, True)
        return success_json({"content": content})
        # query = request.args.get("query")
        # keywords = self.jieba_service.extract_keywords(query)
        # return success_json({"keywords": keywords})
        # vectors = self.embeddings_service.embeddings.embed_query(query)
        # return success_json({"vectors": vectors})

    def hit(self, dataset_id: UUID):
        """根據傳遞的知識庫id+檢索參數執行召回測試"""
        # 1.提取請求的數據並校驗
        req = HitReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務執行檢索策略
        hit_result = self.dataset_service.hit(dataset_id, req)

        return success_json(hit_result)

    def get_dataset_queries(self, dataset_id: UUID):
        """根據傳遞的知識庫id獲取最近的10條查詢記錄"""
        dataset_queries = self.dataset_service.get_dataset_queries(dataset_id)
        resp = GetDatasetQueriesResp(many=True)
        return success_json(resp.dump(dataset_queries))

    def create_dataset(self):
        """創建知識庫"""
        # 1.提取請求的數據並校驗
        req = CreateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建知識庫
        self.dataset_service.create_dataset(req)

        return success_message(f"知識庫已經成功創建")

    def get_dataset(self, dataset_id: UUID):
        """根據知識庫ID獲取詳情"""
        dataset = self.dataset_service.get_dataset(dataset_id)
        resp = GetDatasetResp()
        return success_json(resp.dump(dataset))

    def update_dataset(self, dataset_id: UUID):
        """根據知識庫ID更新知識庫詳情"""
        # 1.提取請求的數據並校驗
        req = UpdateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建知識庫
        self.dataset_service.update_dataset(dataset_id, req)

        return success_message(f"知識庫已經成功更新")

    def delete_dataset(self, dataset_id: UUID):
        """根據傳遞的知識庫id刪除知識庫"""
        self.dataset_service.delete_dataset(dataset_id)
        return success_message("刪除知識庫成功")

    @login_required
    def get_dataset_with_page(self):
        """獲取知識庫分頁＆搜尋列表數據"""
        # 1.提取query數據並校驗
        req = GetDatasetsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        datasets, paginator = self.dataset_service.get_dataset_with_page(req)

        resp = GetDatasetsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))
