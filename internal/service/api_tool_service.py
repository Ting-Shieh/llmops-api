#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/12 下午11:13
@Author : zsting29@gmail.com
@File   : api_tool_service.py
"""
import json
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.exception import ValidateErrorException, NotFoundException
from internal.model import ApiToolProvider, ApiTool
from internal.schema.api_tool_schema import CreateApiToolReq
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class ApiToolService:
    """自定義API插件服務"""
    db: SQLAlchemy

    def create_api_tool(self, req: CreateApiToolReq) -> None:
        """根據傳遞的請求創建自定義API工具"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "12326394kajhdfugoudncj83"

        # 1.檢驗並提取openapi_schema對應的數據
        openapi_schema = self.parse_openapi_schema(req.openapi_schema)

        # 2.查詢當前登入的帳號是否已經創建相同名稱的工具提供者，如果是則拋出錯誤
        api_tool_provider = self.db.session.query(ApiToolProvider).filter_by(
            account_id=account_id,
            name=req.name.data,
        ).one_or_none()
        if api_tool_provider:
            raise ValidateErrorException(f"該工具提供者名字{req.name.data}已存在")

        # 3.開啟數據庫的自動提交
        with self.db.auto_commit():
            # 4.首先創建工具提供者，並獲取工具提供者的id資訊，然後在創建工具資訊
            api_tool_provider = ApiToolProvider(
                account_id=account_id,
                name=req.name.data,
                icon=req.icon.data,
                description=openapi_schema.description,
                openapi_schema=req.openapi_schema.data,
                headers=req.headers.data
            )
            self.db.session.add(api_tool_provider)
            self.db.session.flush()

            # 5.創建API工具並關聯api_tool_provider
            for path, path_item in openapi_schema.paths.items():
                for method, method_item in path_item.items():
                    api_tol = ApiTool(
                        account_id=account_id,
                        provider_id=api_tool_provider.id,
                        name=method_item.get("operationId"),
                        description=method_item.get("description"),
                        url=f"{openapi_schema.server}{path}",
                        method=method,
                        parameters=method_item.get("parameters", []),
                    )
                    self.db.session.add(api_tol)

        # 4.

        # 5.
        pass

    def get_api_tool_provider(self, provider_id: UUID) -> ApiToolProvider:
        """根據provider_id獲取工具提供者的原始訊息"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "12326394kajhdfugoudncj83"

        # 1.查詢數據庫獲取對應數據
        api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)

        # 2.檢驗數據是否為空，並判斷該數據是否屬於當前帳號
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("該工具提供者不存在")

        return api_tool_provider

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
