#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/5 上午8:12
@Author : zsting29@gmail.com
@File   : document_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.schema.document_schema import CreateDocumentsReq, CreateDocumentsResp
from internal.service import DocumentService
from pkg.response import validate_error_json, success_json


@inject
@dataclass
class DocumentHandler:
    """文檔處理器"""
    document_service: DocumentService

    def create_documents(self, dataset_id: UUID):
        """知識庫新增/上傳文件列表"""

        # 1.提取請求並校驗
        req = CreateDocumentsReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務並創建文件，返回文件列表資訊+處理批次
        documents, batch = self.document_service.create_documents(dataset_id, **req.data)

        # 3.生成響應結構並返回
        resp = CreateDocumentsResp()

        return success_json(resp.dump((documents, batch)))

    def get_documents_status(self, dataset_id: UUID, batch: str):
        """根據傳遞的知識庫id+批處理標識獲取文件的狀態"""
        documents_status = self.document_service.get_documents_status(dataset_id, batch)

        return success_json(documents_status)
