#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/17 下午10:43
@Author : zsting29@gmail.com
@File   : RunBindTest.py
"""
import dotenv
from langchain_community.tools.openai_dalle_image_generation import OpenAIDALLEImageGenerationTool
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

dalle = OpenAIDALLEImageGenerationTool(api_wrapper=DallEAPIWrapper(model="dall-e-3"))

llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools([dalle], tool_choice="openai_dalle")  # tool_choice 工具名

chain = llm_with_tools | (lambda msg: msg.tool_calls[0].get("args")) | dalle

print(chain.invoke("幫我畫一張老奶奶坐在公園的長椅上休息的圖片，老奶奶需要手持拐杖"))
