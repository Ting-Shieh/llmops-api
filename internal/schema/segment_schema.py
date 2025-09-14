#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/10 下午11:21
@Author : zsting29@gmail.com
@File   : segment_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField, BooleanField
from wtforms.validators import Optional, ValidationError, DataRequired

from internal.lib.helper import datetime_to_timestamp
from internal.model import Segment
from pkg.paginator import PaginatorReq
from .schema import ListField


class GetSegmentsWithPageReq(PaginatorReq):
    """獲取文件片段列表請求"""
    search_word = StringField("search_word", default="", validators=[
        Optional()
    ])


class GetSegmentsWithPageResp(Schema):
    """獲取文件片段列表響應結構"""
    id = fields.UUID(dump_default="")
    document_id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    position = fields.Integer(dump_default=0)
    content = fields.String(dump_default="")
    keywords = fields.List(fields.String, dump_default=[])
    character_count = fields.Integer(dump_default=0)
    token_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    enabled = fields.Boolean(dump_default=False)
    disabled_at = fields.Integer(dump_default=0)
    status = fields.String(dump_default="")
    error = fields.String(dump_default="")
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Segment, **kwargs):
        return {
            "id": data.id,
            "document_id": data.document_id,
            "dataset_id": data.dataset_id,
            "position": data.position,
            "content": data.content,
            "keywords": data.keywords,
            "character_count": data.character_count,
            "token_count": data.token_count,
            "hit_count": data.hit_count,
            "enabled": data.enabled,
            "disabled_at": datetime_to_timestamp(data.disabled_at),
            "status": data.status,
            "error": data.error,
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class GetSegmentResp(Schema):
    """獲取文件詳情響應結構"""
    id = fields.UUID(dump_default="")
    document_id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    position = fields.Integer(dump_default=0)
    content = fields.String(dump_default="")
    keywords = fields.List(fields.String, dump_default=[])
    character_count = fields.Integer(dump_default=0)
    token_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    hash = fields.String(dump_default="")
    enabled = fields.Boolean(dump_default=False)
    disabled_at = fields.Integer(dump_default=0)
    status = fields.String(dump_default="")
    error = fields.String(dump_default="")
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Segment, **kwargs):
        return {
            "id": data.id,
            "document_id": data.document_id,
            "dataset_id": data.dataset_id,
            "position": data.position,
            "content": data.content,
            "keywords": data.keywords,
            "character_count": data.character_count,
            "token_count": data.token_count,
            "hit_count": data.hit_count,
            "hash": data.hash,
            "enabled": data.enabled,
            "disabled_at": datetime_to_timestamp(data.disabled_at),
            "status": data.status,
            "error": data.error,
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class UpdateSegmentEnabledReq(FlaskForm):
    """更新文件片段啟用狀態請求"""
    enabled = BooleanField("enabled")

    def validate_enabled(self, field: BooleanField) -> None:
        """校驗文件啟用狀態enabled"""
        if not isinstance(field.data, bool):
            raise ValidationError("enabled狀態不能為空且必須為布林值")


class CreateSegmentReq(FlaskForm):
    """創建文件片段請求結構"""
    content = StringField("content", validators=[
        DataRequired("片段內容不能為空")
    ])
    keywords = ListField("keywords")

    def validate_keywords(self, field: ListField) -> None:
        """校驗關鍵字列表，涵蓋長度不能為空，預設為值為空列表"""
        # 1.校驗數據類型+非空
        if field.data is None:
            field.data = []
        if not isinstance(field.data, list):
            raise ValidationError("關鍵字列表格式必須是數組")

        # 2.校驗數據的長度，最長不能超過10個關鍵字
        if len(field.data) > 10:
            raise ValidationError("關鍵字長度範圍數量在1-10")

        # 3.循環校驗關鍵字資訊，關鍵字必須是字串
        for keyword in field.data:
            if not isinstance(keyword, str):
                raise ValidationError("關鍵字必須是字串")

        # 4.刪除重複數據並更新
        field.data = list(dict.fromkeys(field.data))


class UpdateSegmentReq(FlaskForm):
    """更新文件片段請求"""
    content = StringField("content", validators=[
        DataRequired("片段內容不能為空")
    ])
    keywords = ListField("keywords")

    def validate_keywords(self, field: ListField) -> None:
        """校驗關鍵字列表，涵蓋長度不能為空，預設為值為空列表"""
        # 1.校驗數據類型+非空
        if field.data is None:
            field.data = []
        if not isinstance(field.data, list):
            raise ValidationError("關鍵字列表格式必須是數組")

        # 2.校驗數據的長度，最長不能超過10個關鍵字
        if len(field.data) > 10:
            raise ValidationError("關鍵字長度範圍數量在1-10")

        # 3.循環校驗關鍵字資訊，關鍵字必須是字串
        for keyword in field.data:
            if not isinstance(keyword, str):
                raise ValidationError("關鍵字必須是字串")

        # 4.刪除重複數據並更新
        field.data = list(dict.fromkeys(field.data))
