#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/27 下午3:16
@Author : zsting29@gmail.com
@File   : model_batch.py
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
ai_messages = llm.batch([
    prompt.invoke({"query": "現在時間?"}),
    prompt.invoke({"query": "請講一個冷笑話"}),
])

for m in ai_messages:
    print(m)
