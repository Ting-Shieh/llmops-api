#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/28 下午5:25
@Author : zsting29@gmail.com
@File   : app_schema.py
"""
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length


class CompletionReq(FlaskForm):
    """基礎聊天接口請求驗證"""
    # required, max length=2000
    query = StringField("query", validators=[
        DataRequired(message="用戶提問為必填"),
        Length(max=2000, message="用戶的提問最大長度為2000"),
    ])
