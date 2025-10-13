#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/13 下午11:48
@Author : zsting29@gmail.com
@File   : account_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, regexp, Length, URL

from internal.lib.helper import datetime_to_timestamp
from internal.model import Account
from pkg.password import password_pattern


class GetCurrentUserResp(Schema):
    """獲取當前登入帳號資訊響應"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    email = fields.String(dump_default="")
    avatar = fields.String(dump_default="")
    last_login_at = fields.Integer(dump_default=0)
    last_login_ip = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Account, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "email": data.email,
            "avatar": data.avatar,
            "last_login_at": datetime_to_timestamp(data.last_login_at),
            "last_login_ip": data.last_login_ip,
            "created_at": datetime_to_timestamp(data.created_at),
        }


class UpdatePasswordReq(FlaskForm):
    """更新帳號密碼請求"""
    password = StringField("password", validators=[
        DataRequired("登錄密碼不能為空"),
        regexp(regex=password_pattern, message="密碼最少包含一個字母、一個數字，並且長度是8-16"),
    ])


class UpdateNameReq(FlaskForm):
    """更新帳號名稱請求"""
    name = StringField("name", validators=[
        DataRequired("帳號名字不能為空"),
        Length(min=3, max=30, message="帳號名稱長度在3-30位"),
    ])


class UpdateAvatarReq(FlaskForm):
    """更新帳號頭像請求"""
    avatar = StringField("avatar", validators=[
        DataRequired("帳號頭像不能為空"),
        URL("帳號頭像必須是URL圖片地址"),
    ])
