#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/17 上午12:46
@Author : zsting29@gmail.com
@File   : ＧoogleSearchTool.py
"""
import dotenv
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from pydantic import BaseModel, Field

dotenv.load_dotenv()


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="執行Google Search 查詢語句")


google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "一个低成本的谷歌搜索API。"
        "当你需要回答有关时事的问题时，可以调用该工具。"
        "该工具的输入是搜索查询语句。"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)

# print(google_serper.invoke("台積電現在股價多少"))
