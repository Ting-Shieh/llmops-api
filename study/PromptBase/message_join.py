#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/19 下午2:42
@Author : zsting29@gmail.com
@File   : message_join.py
"""

from langchain_core.prompts import ChatPromptTemplate

system_chat_prompt = ChatPromptTemplate.from_messages([
    # 角色, 提問
    ("system", "你是OpenAI開發的聊天機器人，請根據用戶提問進行回覆，我叫{username}。"),
])
human_chat_prompt = ChatPromptTemplate.from_messages([("human", "{query}")])
chat_prompt = system_chat_prompt + human_chat_prompt
print(chat_prompt)
print(chat_prompt.invoke({"username": "Ting", "query": "你可以提供什麼協助"}))
