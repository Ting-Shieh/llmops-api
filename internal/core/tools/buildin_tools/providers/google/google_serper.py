#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/5 下午3:45
@Author : zsting29@gmail.com
@File   : google_serper.py
"""
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class GoogleSerperArgsSchema(BaseModel):
    """Google Serper API Search參數描述"""
    query: str = Field(description="需要檢索查詢的語句．")


@add_attribute("args_schema", GoogleSerperArgsSchema)
def google_serper(**kwargs) -> BaseTool:
    """Google Serper Search"""
    return GoogleSerperRun(
        name="google_serper",
        description=(
            "一個低成本的Google搜索API。"
            "當你需要回答有關時事的問題時，可以調用該工具。"
            "該工具的輸入是搜索查詢語句。"
        ),
        args_schema=GoogleSerperArgsSchema,
        api_wrapper=GoogleSerperAPIWrapper(),
    )
