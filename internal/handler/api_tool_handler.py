#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/12 下午11:00
@Author : zsting29@gmail.com
@File   : api_tool_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from injector import inject

from internal.schema.api_tool_schema import ValidateOpenAPISchemaReq, CreateApiToolReq, GetApiToolProviderResp, \
    GetApiToolResp, GetApiToolProvidersWithPageReq, GetApiToolProvidersWithPageResp, UpdateApiToolProviderReq
from internal.service import ApiToolService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiToolHandler:
    api_tool_service: ApiToolService
    """自定義API插件處理器"""

    def create_api_tool_provider(self):
        """創建自定義API工具"""
        # 1.提取請求的數據並校驗
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建API工具
        self.api_tool_service.create_api_tool_provider(req)

        return success_message("創建自定義API插件工具")

    def update_api_tool_provider(self, provider_id: UUID):
        """更新自定義API工具提供者訊息"""
        req = UpdateApiToolProviderReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.api_tool_service.update_api_tool_provider(provider_id, req)
        return success_message("更新自定義API插件成功")

    def get_api_tool_provider(self, provider_id: UUID):
        """根據provider_id獲取工具提供者的原始訊息"""
        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id)

        resp = GetApiToolProviderResp()

        return success_json(resp.dump(api_tool_provider))

    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """根據provider_id+tool_name獲取工具的詳情訊息"""
        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name)

        resp = GetApiToolResp()

        return success_json(resp.dump(api_tool))

    def delete_api_tool_provider(self, provider_id: UUID):
        """根據provider_id刪除對應自定義API工具提供者訊息"""
        api_tool_provider = self.api_tool_service.delete_api_tool_provider(provider_id)

        return success_message("刪除自定義API插件成功。Delete the custom API plugin successfully.")

    def get_api_tool_providers_with_page(self):
        """獲取API工具提供者列表訊息，該接口支持分頁"""
        req = GetApiToolProvidersWithPageReq(request.args)

        if not req.validate():
            return validate_error_json(req.errors)

        api_tool_providers, paginator = self.api_tool_service.get_api_tool_providers_with_page(req)

        resp = GetApiToolProvidersWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(api_tool_providers), paginator=paginator))

    def validate_openapi_schema(self):
        """校驗傳遞的openapi_schema字符串是否正確"""
        # 1. 提取前端的數據並校驗
        req = ValidateOpenAPISchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務並解析傳遞的數據
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)

        return success_message("數據校驗成功")
