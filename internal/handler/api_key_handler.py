#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/25 下午11:54
@Author : zsting29@gmail.com
@File   : api_key_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.api_key_schema import (
    CreateApiKeyReq,
    UpdateApiKeyReq,
    UpdateApiKeyIsActiveReq,
    GetApiKeysWithPageResp,
)
from internal.service import ApiKeyService
from pkg.paginator import PaginatorReq, PageModel
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiKeyHandler:
    """API秘鑰處理器"""
    api_key_service: ApiKeyService

    @login_required
    def create_api_key(self):
        """創建API秘鑰"""
        # 1.提取請求並校驗
        req = CreateApiKeyReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建秘鑰
        self.api_key_service.create_api_key(req, current_user)

        return success_message("創建API秘鑰成功")

    @login_required
    def delete_api_key(self, api_key_id: UUID):
        """根據傳遞的id刪除API秘鑰"""
        self.api_key_service.delete_api_key(api_key_id, current_user)
        return success_message("刪除API秘鑰成功")

    @login_required
    def update_api_key(self, api_key_id: UUID):
        """根據傳遞的資訊更新API秘鑰"""
        # 1.提取請求並校驗
        req = UpdateApiKeyReq()
        print(req.data)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新秘鑰
        self.api_key_service.update_api_key(api_key_id, current_user, **req.data)

        return success_message("更新API秘鑰成功")

    @login_required
    def update_api_key_is_active(self, api_key_id: UUID):
        """根據傳遞的資訊更新API秘鑰啟用狀態"""
        # 1.提取請求並校驗
        req = UpdateApiKeyIsActiveReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新秘鑰是否啟用
        self.api_key_service.update_api_key(api_key_id, current_user, **req.data)

        return success_message("更新API秘鑰啟用狀態成功")

    @login_required
    def get_api_keys_with_page(self):
        """獲取當前登入帳號的API秘鑰分頁列表資訊"""
        # 1.提取請求並校驗
        req = PaginatorReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務獲取數據
        api_keys, paginator = self.api_key_service.get_api_keys_with_page(req, current_user)

        # 3.構建響應結構並返回
        resp = GetApiKeysWithPageResp(many=True)

        return success_json(
            PageModel(
                list=resp.dump(api_keys),
                paginator=paginator
            )
        )
