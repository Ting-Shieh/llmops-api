#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/27 下午2:52
@Author : zsting29@gmail.com
@File   : llm_chatmodel_use.py
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
ai_message = llm.invoke(prompt.invoke({"query": "現在時間?"}))
print(ai_message.content)
print(ai_message.type)
print(ai_message.response_metadata)
