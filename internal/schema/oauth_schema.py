#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/13 下午11:40
@Author : zsting29@gmail.com
@File   : oauth_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms import StringField
from wtforms.validators import DataRequired


class AuthorizeReq(FlaskForm):
    """第三方授權認證請求體"""
    code = StringField("code", validators=[DataRequired("code代碼不能為空")])


class AuthorizeResp(Schema):
    """第三方授權認證響應結構"""
    access_token = fields.String()
    expire_at = fields.Integer()
