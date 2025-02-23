#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/2/20 下午10:59
@Author : zsting29@gmail.com
@File   : BaseChatHistory.py
"""
import dotenv
from langchain_community.chat_message_histories import FileChatMessageHistory
from openai import OpenAI

dotenv.load_dotenv()
client = OpenAI()
chat_history = FileChatMessageHistory("./memory.txt")

# 創建一個死循環用於人機對話
while True:
    # 獲取人輸入
    query = input("Human: ")

    if query == 'q':
        break

    system_prompt = (
        "你是一個強大的聊天機器人，請依據對應的上下文和用戶提問解決問題 \n\n"
        f"<context>{chat_history}</context> \n\n"
    )
    res = client.chat.completions.create(
        model='gpt-4-turbo',
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        stream=True
    )

    print("AI: ", flush=True, end="")
    ai_content = ""
    for chunk in res:
        # print('>', chunk)
        content = chunk.choices[0].delta.content
        if content is None:
            break
        ai_content += content
        print(content, flush=True, end="")
    chat_history.add_user_message(query)
    chat_history.add_ai_message(ai_content)
    print("")
