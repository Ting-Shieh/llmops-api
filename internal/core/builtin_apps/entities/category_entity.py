#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/2 上午12:21
@Author : zsting29@gmail.com
@File   : category_entity.py
"""
from langchain_core.pydantic_v1 import BaseModel, Field


class CategoryEntity(BaseModel):
    """內建工具分類實體"""
    category: str = Field(default="")  # 分類唯一標識
    name: str = Field(default="")  # 分類對應的名稱
