#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/9 下午10:32
@Author : zsting29@gmail.com
@File   : buildin_tool_service.py
"""
import mimetypes
import os.path
from dataclasses import dataclass
from typing import Any

from flask import current_app
from injector import inject
from langchain_core.pydantic_v1 import BaseModel

from internal.core.tools.buildin_tools.categories import BuildinCategoryManager
from internal.core.tools.buildin_tools.providers import BuildinProviderManager
from internal.exception import NotFoundException


@inject
@dataclass
class BuildinToolService:
    """內置工廠服務"""
    buildin_provider_manager: BuildinProviderManager
    buildin_category_manager: BuildinCategoryManager

    def get_buildin_tools(self):
        """獲取LLMOps所有的內置工具訊息和提供商訊息"""
        # 1.獲取獲取所有的提供商
        providers = self.buildin_provider_manager.get_providers()

        # 2.遍歷所有提供商並提取工具訊息
        buildin_tools = []
        for provider in providers:
            provider_entity = provider.provider_entity
            buildin_tool = {
                **provider_entity.dict(exclude={"icon"}),
                "tools": []
            }
            # 3.遍歷提取提供商的所有工具實體
            for tool_entity in provider.get_tool_entities():
                # 4.從提供商中獲取工具函數
                tool = provider.get_tool(tool_entity.name)

                # 5.構建工具實體訊息
                tool_dict = {
                    **tool_entity.dict(),
                    "inputs": self.get_tool_inputs(tool)
                }
                buildin_tool["tools"].append(tool_dict)

            buildin_tools.append(buildin_tool)
        return buildin_tools

    def get_provider_tools(self, provider_name: str, tool_name: str):
        """根據傳遞的提供商名稱和工具名稱獲取指定工具訊息"""
        # 1.獲取內置的提供商
        provider = self.buildin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"This provider {provider_name} doesn't exist.")

        # 2.獲取該提供商下對應的工具
        tool_entity = provider.get_tool_entity(tool_name)
        if tool_entity is None:
            raise NotFoundException(f"This tool {tool_entity} doesn't exist.")

        # 3.組裝提供商和工具的實體訊息
        provider_entity = provider.provider_entity
        tool = provider.get_tool(tool_name)
        buildin_tool = {
            "provider": {**provider_entity.dict(exclude={"icon", "created_at"})},
            **tool_entity.dict(),
            "created_at": provider_entity.created_at,
            "inputs": self.get_tool_inputs(tool)
        }
        return buildin_tool

    def get_provider_icon(self, provider_name: str) -> tuple[bytes, str]:
        """
        根據傳遞的提供商名稱獲取icon圖標流訊息
        :param provider_name:提供商名稱
        :return:
        """
        # 1.獲取對應的工具提供商
        provider = self.buildin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"This provider {provider_name} doesn't exist.")

        # 2.獲取項目得根路徑訊息
        root_path = os.path.dirname(os.path.dirname(current_app.root_path))

        # 3.拼接得到提供商所在的資料夾
        provider_path = os.path.join(
            root_path,
            "internal", "core", "tools", "buildin_tools", "providers", provider_name
        )

        # 4.拼接得到icon對應的路徑
        icon_path = os.path.join(
            provider_path,
            "_asset", provider.provider_entity.icon
        )

        # 5.檢測icon是否存在
        if not os.path.exists(icon_path):
            raise NotFoundException(f"This provider {provider_name} don't provide icon.")

        # 6.讀取icon的類型
        mimetype, _ = mimetypes.guess_type(icon_path)
        mimetype = mimetype or "application/octet-stream"

        # 7.讀取icon的字節數據
        with open(icon_path, "rb") as f:
            byte_data = f.read()
            return byte_data, mimetype

    def get_categories(self) -> list[str, Any]:
        """獲取所有內置提供商的分類訊息(涵蓋category, name, icon)"""
        category_map = self.buildin_category_manager.get_category_map()
        return [{
            "name": category["entity"].name,
            "category": category["entity"].category,
            "icon": category["icon"],
        } for category in category_map.values()
        ]

    @classmethod
    def get_tool_inputs(cls, tool) -> list:
        """根據傳入的工具獲取inputs訊息"""
        inputs = []
        # 檢測工具是否有args_schema這個屬性，並且是BaseModel的子類
        if hasattr(tool, "args_schema") and issubclass(tool.args_schema, BaseModel):
            # 使用 Pydantic v1 的 __fields__ 屬性
            for field_name, model_field in tool.args_schema.__fields__.items():
                inputs.append({
                    "name": field_name,
                    "description": model_field.field_info.description or "",
                    "required": model_field.required,
                    "type": model_field.outer_type_.__name__,
                })
        return inputs
