#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午2:30
@Author : zsting29@gmail.com
@File   : app_handler.py
"""
import uuid
from dataclasses import dataclass

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.schema.app_schema import CompletionReq
from internal.service import AppService
from pkg.response import success_json, validate_error_json, success_message


@inject
@dataclass
class AppHandler:
    """應用控制器"""
    app_service: AppService

    def create_app(self):
        """調用服務創建新的App紀錄"""
        app = self.app_service.create_app()
        return success_message(f"應用已經成功創建，id為{app.id}")

    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_message(f"應用已經成功獲取，應用名稱為{app.name}")

    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)
        return success_message(f"應用已經成功修改，修改後的應用名稱為{app.name}")

    def delete_app(self, id: uuid.UUID):
        app = self.app_service.delete_app(id)
        return success_message(f"應用已經成功刪除，id為{app.id}")

    def completion(self):
        """聊天接口"""
        # 1.獲取接口的參數
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        prompt = ChatPromptTemplate.from_template("{query}")

        # 2.構建OpenAI客戶端，並發起請求
        llm = ChatOpenAI(model="gpt-4o")

        # 3.得到請求響應，然後將OpenAI的響應傳遞給前端
        ai_message = llm.invoke(
            prompt.invoke({"query": req.query.data})
        )

        parser = StrOutputParser()

        # 4.解析響應內容
        content = parser.invoke(ai_message)

        return success_json({"content": content})

    def ping(self):
        return {"ping": "pong"}
