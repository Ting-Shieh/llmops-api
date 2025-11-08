#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/2 下午6:56
@Author : zsting29@gmail.com
@File   : ai_schema.py
"""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, UUID, Length


class GenerateSuggestedQuestionsReq(FlaskForm):
    """生成建議問題列表請求結構體"""
    message_id = StringField("message_id", validators=[
        DataRequired("消息id不能為空"),
        UUID(message="消息id格式必須為uuid")
    ])


class OptimizePromptReq(FlaskForm):
    """最佳化預設prompt請求結構體"""
    prompt = StringField("prompt", validators=[
        DataRequired("預設prompt不能為空"),
        Length(max=2000, message="預設prompt的長度不能超過2000個字元")
    ])
