#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/29 下午1:38
@Author : zsting29@gmail.com
@File   : StrOutputParseUse.py
"""
from datetime import datetime

import dotenv
from langchain_core.output_parsers import StrOutputParser
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

parser = StrOutputParser()
content = parser.parse("Coding Dream")  # 傳什麼返回什麼
print(content)
content2 = parser.invoke(llm.invoke(prompt.invoke({"query": "現在時間?"})))
print(content2)
