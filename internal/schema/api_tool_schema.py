#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/12 下午11:04
@Author : zsting29@gmail.com
@File   : api_tool_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL, ValidationError, Optional

from internal.model import ApiToolProvider, ApiTool
from internal.schema import ListField
from pkg.paginator import PaginatorReq


class ValidateOpenAPISchemaReq(FlaskForm):
    """校驗OpenAPI規範字符串請求"""

    openapi_schema = StringField(
        "openapi_schema",
        validators=[
            DataRequired(message="openapi_schema字符串不得為空")
        ]
    )


class CreateApiToolReq(FlaskForm):
    """校驗創建自定義API工具"""
    name = StringField(
        "name",
        validators=[
            DataRequired(message="工具提供者名字不得為空"),
            Length(min=1, max=30, message="工具提供者名字長度在1-30")
        ]
    )

    icon = StringField(
        "icon",
        validators=[
            DataRequired(message="工具提供者的圖標不得為空"),
            URL(message="工具提供者的圖標必須是URL連接")
        ]
    )

    openapi_schema = StringField(
        "openapi_schema",
        validators=[
            DataRequired(message="openapi_schema字符串不得為空")
        ]
    )

    headers = ListField("headers")

    @classmethod
    def validate_headers(cls, form, field):
        """校驗headers請求的數據是否正確, 涵蓋列表校驗, 列表元素校驗．"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationError("headers中每一個元素都必須是字典")
            if set(header.keys()) != {"key", "value"}:
                raise ValidationError("headers中每一個元素都必須包含key/value兩個屬性，不允許有其他屬性")


class GetApiToolProviderResp(Schema):
    """獲取API工具提供者響應訊息"""
    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    description = fields.String()
    openapi_schema = fields.String()
    headers = fields.List(fields.Dict, default=[])
    created_at = fields.Integer(default=0)

    # 映射數據
    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        """"""
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "openapi_schema": data.openai_schema,
            "headers": data.headers,
            "created_at": int(data.created_at.timestamp()),
        }


class GetApiToolResp(Schema):
    """獲取API工具參數詳情響應訊息"""
    id = fields.UUID()
    name = fields.String()
    description = fields.String()
    inputs = fields.List(fields.Dict, default=[])
    provider = fields.Dict()

    # 映射數據
    @pre_dump
    def process_data(self, data: ApiTool, **kwargs):
        provider = data.provider
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "inputs": [{k: v for k, v in parameter.items() if k != 'in'} for parameter in data.parameters],
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "icon": provider.icon,
                "description": provider.description,
                "headers": provider.headers,
            },
            "created_at": int(data.created_at.timestamp()),
        }


class GetApiToolProvidersWithPageReq(PaginatorReq):
    """獲取API工具提供者分頁列表請求"""
    search_word = StringField(
        "search_word",
        validators=[
            Optional(),
        ]
    )


class GetApiToolProvidersWithPageResp(Schema):
    """獲取API工具提供者分頁列表數據檢驗"""
    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    description = fields.String()
    headers = fields.List(fields.Dict, default=[])
    tools = fields.List(fields.Dict, default=[])
    created_at = fields.Integer(default=0)

    # 映射數據
    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        tools = data.tools
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "headers": data.headers,
            "tools": [{
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "inputs": [{k: v for k, v in parameter.items() if k != 'in'} for parameter in tool.parameters],
            } for tool in tools],
            "created_at": int(data.created_at.timestamp()),
        }
