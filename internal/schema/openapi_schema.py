#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/26 下午11:39
@Author : zsting29@gmail.com
@File   : openapi_schema.py
"""
import uuid
from urllib.parse import urlparse

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, UUID, Optional, ValidationError

from .schema import ListField


class OpenAPIChatReq(FlaskForm):
    """開放API聊天介面請求結構體"""
    app_id = StringField("app_id", validators=[
        DataRequired("應用id不能為空"),
        UUID("應用id格式必須為UUID"),
    ])
    end_user_id = StringField("end_user_id", default="", validators=[
        Optional(),
        UUID("終端用戶id必須為UUID"),
    ])
    conversation_id = StringField("conversation_id", default="")
    query = StringField("query", default="", validators=[
        DataRequired("用戶提問query不能為空"),
    ])
    image_urls = ListField("image_urls", default=[])
    stream = BooleanField("stream", default=True)

    def validate_conversation_id(self, field: StringField) -> None:
        """自訂校驗conversation_id函數"""
        # 1.檢測是否傳遞數據，如果傳遞了，則類型必須為UUID
        if field.data:
            try:
                uuid.UUID(field.data)
            except Exception as _:
                raise ValidationError("會話id格式必須為UUID")

            # 2.終端用戶id是不是為空
            if not self.end_user_id.data:
                raise ValidationError("傳遞會話id則終端用戶id不能為空")

    def validate_image_urls(self, field: ListField) -> None:
        """校驗傳遞的圖片URL連結列表"""
        # 1.校驗數據類型如果為None則設置預設值空列表
        if not isinstance(field.data, list):
            return []

        # 2.校驗數據的長度，最多不能超過5條URL記錄
        if len(field.data) > 5:
            raise ValidationError("上傳的圖片數量不能超過5，請核實後重試")

        # 3.循環校驗image_url是否為URL
        for image_url in field.data:
            result = urlparse(image_url)
            if not all([result.scheme, result.netloc]):
                raise ValidationError("上傳的圖片URL地址格式錯誤，請核實後重試")
