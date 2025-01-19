#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/19 下午1:49
@Author : zsting29@gmail.com
@File   : prompt_base_use.py
"""
from datetime import datetime

from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder

prompt = PromptTemplate.from_template("請講一個關於{subject}的冷笑話")
print(prompt.format(subject="工程師"))
prompt_value = prompt.invoke({"subject": "工程師"})
print(prompt_value.to_string())
print(prompt_value.to_messages())
print("===========================")
chat_prompt = ChatPromptTemplate.from_messages([
    # 角色, 提問
    ("system", "你是OpenAI開發的聊天機器人，請根據用戶提問進行回覆，當前時間為:{now}。"),
    # 有時候可能還有其他的消息，但是不確定
    MessagesPlaceholder("chat_history"),
    #
    HumanMessagePromptTemplate.from_template("請講一個關於{subject}的冷笑話")
]).partial(now=datetime.now())
chat_prompt_value = chat_prompt.invoke({
    # "now": datetime.now(),
    "chat_history": [
        ("human", "My name is Ting."),
        AIMessage("Hello, I'm ChatGPT. May I help you?")
    ],
    "subject": "工程師"
})
print(chat_prompt_value)
print(chat_prompt_value.to_string())
