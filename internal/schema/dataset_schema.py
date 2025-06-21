#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/17 下午10:34
@Author : zsting29@gmail.com
@File   : dataset_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length, URL, Optional

from internal.model import Dataset
from pkg.paginator import PaginatorReq


class CreateDatasetReq(FlaskForm):
    """創建知識庫請求"""
    name = StringField(
        "name",
        validators=[
            DataRequired(message="知識庫名稱不能為空"),
            Length(max=100, message="知識庫名稱長度不能超過100字符")
        ]
    )

    icon = StringField("icon", validators=[
        DataRequired("知識庫圖標不能為空"),
        URL("知識庫圖標必須是圖片URL地址"),
    ])
    description = StringField("description", default="", validators=[
        Optional(),
        Length(max=2000, message="知識庫描述長度不能超過2000字符")
    ])


class GetDatasetResp(Schema):
    """獲取知識庫詳情響應結構"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "hit_count": data.hit_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }


class UpdateDatasetReq(FlaskForm):
    """更新知識庫请求"""
    name = StringField("name", validators=[
        DataRequired("知識庫名稱不能為空"),
        Length(max=100, message="知識庫名稱長度不能超過100字符"),
    ])
    icon = StringField("icon", validators=[
        DataRequired("知識庫圖標不能为空"),
        URL("知識庫圖標必須是圖片URL地址"),
    ])
    description = StringField("description", default="", validators=[
        Optional(),
        Length(max=2000, message="知識庫描述長度不能超過2000字符")
    ])


class GetDatasetsWithPageReq(PaginatorReq):
    """獲取知識庫分頁列請求數據"""
    search_word = StringField("search_word", default="", validators=[
        Optional(),
    ])


class GetDatasetsWithPageResp(Schema):
    """獲取知識庫分頁列表響應數據"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }
