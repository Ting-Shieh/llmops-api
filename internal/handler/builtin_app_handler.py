#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/2 下午9:59
@Author : zsting29@gmail.com
@File   : builtin_app_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.builtin_app_schema import (
    GetBuiltinAppCategoriesResp,
    GetBuiltinAppsResp,
    AddBuiltinAppToSpaceReq,
)
from internal.service import BuiltinAppService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class BuiltinAppHandler:
    """LLMOps內建應用處理器"""
    builtin_app_service: BuiltinAppService

    @login_required
    def get_builtin_app_categories(self):
        """獲取內建應用分類列表資訊"""
        categories = self.builtin_app_service.get_categories()
        resp = GetBuiltinAppCategoriesResp(many=True)
        return success_json(resp.dump(categories))

    @login_required
    def get_builtin_apps(self):
        """獲取所有內建應用列表資訊"""
        builtin_apps = self.builtin_app_service.get_builtin_apps()
        resp = GetBuiltinAppsResp(many=True)
        return success_json(resp.dump(builtin_apps))

    @login_required
    def add_builtin_app_to_space(self):
        """將指定的內建應用添加到個人空間"""
        # 1.提取請求並校驗
        req = AddBuiltinAppToSpaceReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.將指定內建應用模板添加到個人空間
        app = self.builtin_app_service.add_builtin_app_to_space(req.builtin_app_id.data, current_user)

        return success_json({"id": app.id})
