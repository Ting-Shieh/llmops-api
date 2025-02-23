#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/2/19 下午9:02
@Author : zsting29@gmail.com
@File   : remember.py
"""
from typing import Any

import dotenv
from openai import OpenAI

dotenv.load_dotenv()


# 1.max_tokens:判斷是否需要生成新的摘要
# 2.summary: 儲存摘要的訊息
# 3.chat_histories: 儲存歷史對話
# 4.get_num_tokens: 計算傳入文本的token數
# 5.save_context: 儲存新的交流對話
# 6.get_bugger_string: 將歷史對話轉成字符串
# 7.load_memory_variables: 加載記憶變量訊息
# 8.summary_text: 將舊的摘要和傳入的對話生成新摘要
class ConversationSummaryBufferMemory:
    """摘要緩衝混合記憶類"""

    def __init__(
            self,
            summary: str = '',
            chat_histories: list = None,
            max_tokens: int = 300,
    ):
        self.summary = summary
        self.chat_histories = [] if chat_histories is None else chat_histories
        self.max_tokens = max_tokens
        self._client = OpenAI()

    @classmethod
    def get_num_tokens(cls, query: str) -> int:
        """計算傳入query的token數"""
        return len(query)

    def save_context(self, human_query: str, ai_content: str) -> None:
        """保存傳入的新一次對話"""
        self.chat_histories.append({
            "human": human_query,
            "ai": ai_content
        })

        buffer_string = self.get_bugger_string()
        tokens = self.get_num_tokens(buffer_string)

        if tokens > self.max_tokens:
            first_chat = self.chat_histories[0]
            print("新摘要生成中.....")
            self.summary = self.summary_text(
                self.summary,
                f"Human:{first_chat.get('human')}\nAI:{first_chat.get('ai')}"
            )
            print("新摘要生成成功: ", self.summary)
            del self.chat_histories[0]

    def get_bugger_string(self) -> str:
        """將歷史對話轉成字符串"""
        buffer: str = ""
        for chat in self.chat_histories:
            buffer += f"Human:{chat.get('human')}\nAI:{chat.get('ai')}\n\n"
        return buffer.strip()

    def load_memory_variables(self) -> dict[str, Any]:
        """加載記憶變量為一個字典，使格式化到prompt"""
        buffer_string = self.get_bugger_string()
        return {
            "chat_history": f"摘要: {self.summary}\n\n歷史訊息: {buffer_string}\n"
        }

    def summary_text(self, origin_summary: str, new_line: str) -> str:
        """將舊的摘要和傳入的對話生成新摘要"""
        prompt = f""""""

        completion = self._client.chat.completions.create(
            model='gpt-4-turbo',
            messages=[{"role": "user", "content": prompt}],
        )

        return completion.choices[0].message.content


client = OpenAI()

memery = ConversationSummaryBufferMemory("", [], 300)

# 創建一個死循環用於人機對話
while True:
    # 獲取人輸入
    query = input("Human: ")

    if query == 'q':
        break

    memory_variables = memery.load_memory_variables()
    answer_prompt = (
        "你是一個強大的聊天機器人，請依據對應的上下文和用戶提問解決問題 \n\n"
        f"{memory_variables.get('chat_history')} \n\n"
        f"用戶的提問: {query}"
    )

    res = client.chat.completions.create(
        model='gpt-4-turbo',
        messages=[
            {"role": "user", "content": answer_prompt}
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
    print("")
    memery.save_context(query, ai_content)
