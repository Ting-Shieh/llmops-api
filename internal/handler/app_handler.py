#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午2:30
@Author : zsting29@gmail.com
@File   : app_handler.py
"""
from flask import request
from openai import OpenAI

from internal.schema.app_schema import CompletionReq


class AppHandler:
    """應用控制器"""

    def completion(self):
        """聊天接口"""
        # 1.獲取接口的參數
        req = CompletionReq()
        if not req.validate():
            return req.errors
        query = request.json.get("query")
        # 2.構建OpenAI客戶端，並發起請求
        client = OpenAI(
            # api_key="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"
        )
        # 3.得到請求響應，然後將OpenAI的響應傳遞給前端
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你是OpenAI開發的聊天機器人，請根據用戶的輸入回覆對應的訊息．",
                },
                {
                    "role": "user",
                    "content": query,
                },
            ]
        )
        print(completion.choices[0].message)
        content = completion.choices[0].message.content
        return content

    def ping(self):
        return {"ping": "pong"}
