#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/5 上午8:12
@Author : zsting29@gmail.com
@File   : document_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import current_user, login_required
from injector import inject

from internal.schema.document_schema import (
    CreateDocumentsReq,
    CreateDocumentsResp,
    GetDocumentResp,
    UpdateDocumentNameReq,
    GetDocumentsWithPageReq, GetDocumentsWithPageResp, UpdateDocumentEnabledReq
)
from internal.service import DocumentService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class DocumentHandler:
    """文檔處理器"""
    document_service: DocumentService

    @login_required
    def create_documents(self, dataset_id: UUID):
        """知識庫新增/上傳文件列表"""

        # 1.提取請求並校驗
        req = CreateDocumentsReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務並創建文件，返回文件列表資訊+處理批次
        documents, batch = self.document_service.create_documents(dataset_id, **req.data, account=current_user)

        # 3.生成響應結構並返回
        resp = CreateDocumentsResp()

        return success_json(resp.dump((documents, batch)))

    @login_required
    def get_document(self, dataset_id: UUID, document_id: UUID):
        """根據傳遞的知識庫id+文件id更新對應文件的名稱資訊"""
        document = self.document_service.get_document(dataset_id, document_id, current_user)

        resp = GetDocumentResp()

        return success_json(resp.dump(document))

    @login_required
    def update_document_name(self, dataset_id: UUID, document_id: UUID):
        """根據傳遞的知識庫id+文件id更新對應文件的名稱資訊"""
        # 1.提取請求並校驗數據
        req = UpdateDocumentNameReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新文件的名稱資訊
        self.document_service.update_document(dataset_id, document_id, account=current_user, name=req.name.data)

        return success_message("更新文檔名稱成功")

    @login_required
    def get_documents_with_page(self, dataset_id: UUID):
        """根據傳遞的知識庫id獲取文件分頁列表數據"""
        # 1.提取請求數據並校驗
        req = GetDocumentsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務獲取分頁列表數據以及分頁數據
        documents, paginator = self.document_service.get_documents_with_page(dataset_id, req, current_user)

        # 3.構建響應結構並映射
        resp = GetDocumentsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(documents), paginator=paginator))

    @login_required
    def get_documents_status(self, dataset_id: UUID, batch: str):
        """根據傳遞的知識庫id+批處理標識獲取文件的狀態"""
        documents_status = self.document_service.get_documents_status(dataset_id, batch, current_user)

        return success_json(documents_status)

    @login_required
    def update_document_enabled(self, dataset_id: UUID, document_id: UUID):
        """根據傳遞的知識庫id+文件id更新指定文件的啟用狀態"""
        # 1.提取請求並校驗
        req = UpdateDocumentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新指定文件的狀態
        self.document_service.update_document_enabled(dataset_id, document_id, req.enabled.data, current_user)

        return success_message("更改文件啟用狀態成功")

    @login_required
    def delete_document(self, dataset_id: UUID, document_id: UUID):
        """根據傳遞的知識庫id+文件id刪除指定的文件資訊"""
        self.document_service.delete_document(dataset_id, document_id, current_user)

        return success_message("刪除文件成功")
