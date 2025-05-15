#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/12 下午11:13
@Author : zsting29@gmail.com
@File   : api_tool_service.py
"""
import json
from dataclasses import dataclass

from injector import inject

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.exception import ValidateErrorException


@inject
@dataclass
class ApiToolService:
    """自定義API插件服務"""

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
