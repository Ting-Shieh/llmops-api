#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/12 下午11:13
@Author : zsting29@gmail.com
@File   : api_tool_service.py
"""
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.exception import ValidateErrorException, NotFoundException
from internal.model import ApiToolProvider, ApiTool
from internal.schema.api_tool_schema import CreateApiToolReq, GetApiToolProvidersWithPageReq, UpdateApiToolProviderReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..core.tools.api_tools.providers import ApiProviderManager


@inject
@dataclass
class ApiToolService(BaseService):
    """自定義API插件服務"""
    db: SQLAlchemy
    api_provider_manager: ApiProviderManager

    def create_api_tool_provider(self, req: CreateApiToolReq) -> None:
        """根據傳遞的請求創建自定義API工具"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        # 1.檢驗並提取openapi_schema對應的數據
        openapi_schema = self.parse_openapi_schema(req.openapi_schema)

        # 2.查詢當前登入的帳號是否已經創建相同名稱的工具提供者，如果是則拋出錯誤
        api_tool_provider = self.db.session.query(ApiToolProvider).filter_by(
            account_id=account_id,
            name=req.name.data,
        ).one_or_none()
        if api_tool_provider:
            raise ValidateErrorException(f"該工具提供者名字{req.name.data}已存在")

        # 3.首先創建工具提供者，並獲取工具提供者的id資訊，然後在創建工具資訊
        api_tool_provider = self.create(
            ApiToolProvider,
            account_id=account_id,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data
        )

        # 4.創建API工具並關聯api_tool_provider
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account_id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def update_api_tool_provider(self, provider_id, req: UpdateApiToolProviderReq):
        """根據provider_id+req，更新對應的API工具提供者訊息"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        # 1.根據provider_id查找API工具提供者訊息並校驗
        # # api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)
        api_tool_provider = self.get(ApiToolProvider, provider_id)

        # 2.檢驗數據是否為空，並判斷該數據是否屬於當前帳號
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("該工具提供者不存在。The tool provider does not exist.")

        # 3.校驗openapi_schema數據
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 4.檢測當前帳號是否已經創建了同名的工具工具提供者，如果是則拋出錯誤
        check_api_tool_provider = self.db.session.query(ApiToolProvider).filter(
            ApiToolProvider.account_id == account_id,
            ApiToolProvider.name == req.name.data,
            ApiToolProvider.id != api_tool_provider.id
        ).one_or_none()
        if check_api_tool_provider:
            raise ValidateErrorException(
                f"該工具提供者名稱 {req.name.data}已存在。The tool provider's name {req.name.data} exist.")

        # 5.開啟數據庫自動提交
        with self.db.auto_commit():
            # 6.先刪除該工具提供者下的所有工具
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == api_tool_provider.id,
                ApiTool.account_id == account_id,
            ).delete()

        # 6.修改工具提供者訊息
        self.update(
            api_tool_provider,
            name=req.name.data,
            icon=req.icon.data,
            headers=req.headers.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data
        )
        # 7.新增工具訊息從而完成覆蓋更新
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account_id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def get_api_tool_provider(self, provider_id: UUID) -> ApiToolProvider:
        """根據provider_id獲取工具提供者的原始訊息"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        # 1.查詢數據庫獲取對應數據
        api_tool_provider = self.get(ApiToolProvider, provider_id)

        # 2.檢驗數據是否為空，並判斷該數據是否屬於當前帳號
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("該工具提供者不存在。The tool provider does not exist.")

        return api_tool_provider

    def get_api_tool(self, provider_id: UUID, tool_name: str) -> ApiTool:
        """根據provider_id+tool_name獲取工具的詳情訊息"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        api_tool = self.db.session.query(ApiTool).filter_by(
            provider_id=provider_id,
            name=tool_name
        ).one_or_none()

        if api_tool is None or str(api_tool.account_id) != account_id:
            raise NotFoundException("該工具不存在。The tool does not exist.")

        return api_tool

    def delete_api_tool_provider(self, provider_id: UUID):
        """根據provider_id刪除對應自定義API工具提供者訊息"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        # 1.先查找數據，檢測provider_id對應的數據是否存在，權限是否正確
        api_tool_provider = self.get(ApiToolProvider, provider_id)

        # 2.檢驗數據是否為空，並判斷該數據是否屬於當前帳號
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("該工具提供者不存在。The tool provider does not exist.")

        # 4.開啟數據庫的自動提交
        with self.db.auto_commit():
            # 5.先來刪除提供者對應的工具訊息
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account_id
            ).delete()

            # 6.刪除服務提供者
            self.db.session.delete(api_tool_provider)

    def get_api_tool_providers_with_page(
            self,
            req: GetApiToolProvidersWithPageReq
    ) -> tuple[list[Any], Paginator]:
        """獲取自定義API工具服務提供者分頁列表數據"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        # 1.構建分頁數據
        paginator = Paginator(db=self.db, req=req)

        # 2.構建篩選器
        filters = [ApiToolProvider.account_id == account_id]
        if req.search_word.data:
            filters.append(ApiToolProvider.name.ilike(f"%{req.search_word.data}%"))

        # 3.執行分頁並獲取數據
        api_tool_providers = paginator.paginate(
            self.db.session.query(ApiToolProvider).filter(*filters).order_by(desc("created_at"))
        )

        return api_tool_providers, paginator

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> OpenAPISchema:
        """解析傳遞的openapi_schema字符串，如果出錯則拋出錯誤"""
        try:
            data = json.loads(openapi_schema_str.strip())
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateErrorException("傳遞數據必須符合OpenAPI規範的JSON字符串")

        return OpenAPISchema(**data)

    def api_tool_invoke(self):
        # todo: 等待授權認證模塊完成進行切換調整
        provider_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"
        tool_name = "YoudaoSuggests"

        api_tool = self.db.session.query(ApiTool).filter(
            ApiTool.provider_id == provider_id,
            ApiTool.name == tool_name
        ).one_or_none()
        api_tool_provider = api_tool.provider

        from internal.core.tools.api_tools.entities import ToolEntity
        tool = self.api_provider_manager.get_tool(ToolEntity(
            id=provider_id,
            name=tool_name,
            url=api_tool.url,
            method=api_tool.meyhod,
            description=api_tool.description,
            headers=api_tool_provider.headers,
            parameters=api_tool.parameters
        ))
        return tool.invoke({"q": "love", "doctype": "json"})
