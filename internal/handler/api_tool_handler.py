#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/12 下午11:00
@Author : zsting29@gmail.com
@File   : api_tool_handler.py
"""
from dataclasses import dataclass

from injector import inject

from internal.schema.api_tool_schema import ValidateOpenAPISchemaReq, CreateApiToolReq
from internal.service import ApiToolService
from pkg.response import validate_error_json, success_message


@inject
@dataclass
class ApiToolHandler:
    api_tool_service: ApiToolService
    """自定義API插件處理器"""

    def create_api_tool(self):
        """創建自定義API工具"""
        # 1.提取請求的數據並校驗
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json()

        # 2.調用服務創建API工具
        self.api_tool_service.create_api_tool(req)

        return success_message("創建自定義API插件工具")

    def validate_openapi_schema(self):
        """校驗傳遞的openapi_schema字符串是否正確"""
        # 1. 提取前端的數據並校驗
        req = ValidateOpenAPISchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務並解析傳遞的數據
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)

        return success_message("數據校驗成功")
