#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/11 下午2:15
@Author : zsting29@gmail.com
@File   : category_entity.py
"""
from pydantic import BaseModel, field_validator

from internal.exception import FailException


class CategoryEntity(BaseModel):
    """分類實體"""
    category: str  # 分類唯一標誌
    name: str  # 分類名稱
    icon: str  # 分類圖標

    @field_validator("icon")
    def check_icon_extension(cls, value: str):
        """校驗icon的擴展名是不是.svg，若非則拋出錯誤"""
        if not value.endswith(".svg"):
            raise FailException("The category's icon is not in .svg format.")
        return value
