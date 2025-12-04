#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/2 下午10:00
@Author : zsting29@gmail.com
@File   : builtin_app_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, UUID

from internal.core.builtin_apps.entities.builtin_app_entity import BuiltinAppEntity
from internal.core.builtin_apps.entities.category_entity import CategoryEntity


class GetBuiltinAppCategoriesResp(Schema):
    """獲取內建應用分類列表響應"""
    category = fields.String(dump_default="")
    name = fields.String(dump_default="")

    @pre_dump
    def process_data(self, data: CategoryEntity, **kwargs):
        return data.dict()


class GetBuiltinAppsResp(Schema):
    """獲取內建應用實體列表響應"""
    id = fields.String(dump_default="")
    category = fields.String(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    model_config = fields.Dict(dump_default={})
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: BuiltinAppEntity, **kwargs):
        return {
            **data.dict(include={"id", "category", "name", "icon", "description", "created_at"}),
            "model_config": {
                "provider": data.language_model_config.get("provider", ""),
                "model": data.language_model_config.get("model", ""),
            }
        }


class AddBuiltinAppToSpaceReq(FlaskForm):
    """添加內建應用到個人空間請求"""
    builtin_app_id = StringField("builtin_app_id", default="", validators=[
        DataRequired("內建應用id不能為空"),
        UUID("內建工具id格式必須為UUID"),
    ])
