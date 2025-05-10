#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/8 下午9:46
@Author : zsting29@gmail.com
@File   : wikipedia_search.py
"""
from langchain_community.tools import WikipediaQueryRun
from langchain_community.tools.wikipedia.tool import WikipediaQueryInput
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


@add_attribute("args_schema", WikipediaQueryInput)
def wikipedia_search(**kwargs) -> BaseTool:
    """返回維基百科搜索工具"""
    return WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper()
    )
