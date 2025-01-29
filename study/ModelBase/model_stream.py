#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/27 下午3:21
@Author : zsting29@gmail.com
@File   : model_stream.py
"""
from datetime import datetime

import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

# 1. 編排prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是ＯpenAI開發的聊天機器人，請回答用戶問題，現在時間是{now}"),
    ("human", "{query}")
]).partial(now=datetime.now())

# 創建大語言模型
llm = ChatOpenAI(model="gpt-4o")
responses = llm.stream(prompt.invoke({"query": "你能簡單介紹一下LLM和LLMOps嗎？"}))

for chunk in responses:
    print(chunk.content, flush=True, end="")
