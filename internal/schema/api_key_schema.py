#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/12 下午1:43
@Author : zsting29@gmail.com
@File   : api_key_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import fields, Schema, pre_dump
from wtforms import BooleanField, StringField
from wtforms.validators import Length

from internal.lib.helper import datetime_to_timestamp
from internal.model import ApiKey


class CreateApiKeyReq(FlaskForm):
    """創建API秘鑰請求"""
    is_active = BooleanField("is_active")
    remark = StringField("remark", validators=[
        Length(max=100, message="秘鑰備註不能超過100個字元")
    ])


class UpdateApiKeyReq(FlaskForm):
    """更新API秘鑰請求"""
    is_active = BooleanField("is_active")
    remark = StringField("remark", validators=[
        Length(max=100, message="秘鑰備註不能超過100個字元")
    ])


class UpdateApiKeyIsActiveReq(FlaskForm):
    """更新API秘鑰啟用請求"""
    is_active = BooleanField("is_active")


class GetApiKeysWithPageResp(Schema):
    """獲取API秘鑰分頁列表數據"""
    id = fields.UUID(dump_default="")
    api_key = fields.String(dump_default="")
    is_active = fields.Boolean(dump_default=False)
    remark = fields.String(dump_default="")
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: ApiKey, **kwargs):
        return {
            "id": data.id,
            "api_key": data.api_key,
            "is_active": data.is_active,
            "remark": data.remark,
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }
