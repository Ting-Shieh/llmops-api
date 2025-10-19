#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/14 下午11:17
@Author : zsting29@gmail.com
@File   : auth_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms import StringField
from wtforms.validators import DataRequired, Email, Length, regexp

from pkg.password import password_pattern


class PasswordLoginReq(FlaskForm):
    """帳號密碼登入請求結構"""
    email = StringField("email", validators=[
        DataRequired("登錄信箱不能為空"),
        Email("登錄信箱格式錯誤"),
        Length(min=5, max=254, message="登錄信箱長度在5-254個字元"),
    ])
    password = StringField("password", validators=[
        DataRequired("帳號密碼不能為空"),
        regexp(regex=password_pattern, message="密碼最少包含一個字母，一個數字，並且長度為8-16")
    ])


class PasswordLoginResp(Schema):
    """帳號密碼授權認證響應結構"""
    access_token = fields.String()
    expire_at = fields.Integer()
