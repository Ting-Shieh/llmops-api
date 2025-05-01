#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/30 下午5:46
@Author : zsting29@gmail.com
@File   : ReActAgent.py
"""
import dotenv
from langchain_community.tools import GoogleSerperRun
from langchain_community.tools.openai_dalle_image_generation import OpenAIDALLEImageGenerationTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from study.CustomTools.GoogleSearchTool2 import GoogleSerperArgsSchema

dotenv.load_dotenv()
google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "一個低成本的Google搜索API。"
        "當你需要回答有關時事的問題時，可以調用該工具。"
        "該工具的輸入是搜索查詢語句。"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)

dalle = OpenAIDALLEImageGenerationTool(
    api_wrapper=DallEAPIWrapper(model="dall-e-3")
)
tools = [google_serper, dalle]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_react_agent(model=llm, tools=tools)

print(agent.invoke({"messages": [
    ("human", "幫我畫一張老奶奶坐在公園的長椅上休息的圖片")
]}))
