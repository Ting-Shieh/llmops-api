#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/12 下午11:04
@Author : zsting29@gmail.com
@File   : api_tool_schema.py
"""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL, ValidationError

from internal.schema import ListField


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
