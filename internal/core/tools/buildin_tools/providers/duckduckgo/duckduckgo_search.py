#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/7 下午10:33
@Author : zsting29@gmail.com
@File   : duckduckgo_search.py
"""
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


class DuckDuckGoInput(BaseModel):
    query: str = Field(description="需要搜索的查詢語句")


@add_attribute("args_schema", DuckDuckGoInput)
def duckduckgo_search(**kwargs) -> BaseTool:
    """返回DuckDuckGo搜索工具"""
    return DuckDuckGoSearchRun(
        description="一個注重隱私的搜尋工具，當你需要搜索時事時可使用該工具，工具的輸入是一個查詢語句。",
        args_schema=DuckDuckGoInput
    )
