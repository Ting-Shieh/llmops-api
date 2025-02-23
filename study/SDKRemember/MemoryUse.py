#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/2/22 下午9:59
@Author : zsting29@gmail.com
@File   : MemoryUse.py
"""
from operator import itemgetter

import dotenv
from langchain.memory import ConversationBufferWindowMemory
# from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

# 創建記憶
memory = ConversationBufferWindowMemory(
    input_key="query",
    return_messages=True,
    k=2,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是OpenAI开发的聊天机器人，请帮助用户解决问题"),
    MessagesPlaceholder("history"),
    ("human", "{query}")
])

llm = ChatOpenAI(model="gpt-3.5-turbo-16k")

chain = RunnablePassthrough.assign(
    history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
) | prompt | llm | StrOutputParser()

while True:
    query = input("Human: ")

    if query == "q":
        exit(0)

    chain_input = {"query": query}

    print("AI: ", flush=True, end="")
    response = chain.stream(chain_input)
    output = ""
    for chunk in response:
        output += chunk
        print(chunk, flush=True, end="")
    print("\nhistory:", memory.load_memory_variables({}))

    memory.save_context(chain_input, {"output": output})
