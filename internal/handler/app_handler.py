#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午2:30
@Author : zsting29@gmail.com
@File   : app_handler.py
"""
import os
import uuid
from dataclasses import dataclass
from operator import itemgetter
from typing import Dict, Any

from injector import inject
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.memory import BaseMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from langchain_core.tracers import Run
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

    @classmethod
    def _load_memory_variable(cls, input: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """加載記憶變量訊息"""
        # 1.從config獲取configurable
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            return configurable_memory.load_memory_variables(input)
        return {"history": []}

    @classmethod
    def _save_context(cls, run_obj: Run, config: RunnableConfig) -> None:
        """存儲對應的上下文訊息到對應實體中"""
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            configurable_memory.save_context(run_obj.inputs, run_obj.outputs)

    def debug(self, app_id: uuid.UUID):
        """聊天接口"""
        # 1.獲取接口的參數
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.創建prompt與記憶
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一個強大的聊天機器人，能依據用戶提問回覆對應問題"),
            MessagesPlaceholder("history"),
            ("human", "{query}"),
        ])
        print(os.getcwd())
        print(os.path.abspath('.'))
        memory = ConversationBufferWindowMemory(
            k=3,
            input_key="query",
            output_key="output",
            return_messages=True,
            chat_memory=FileChatMessageHistory("../../storage/memory/chat_history.txt")
            # ./storage/memory/chat_history.txt
        )

        # 3.create llm
        llm = ChatOpenAI(model="gpt-3.5-turbo-16k")  # 構建OpenAI客戶端

        # 4..create LCEL
        chain = (RunnablePassthrough.assign(
            history=RunnableLambda(self._load_memory_variable) | itemgetter("history")
        ) | prompt | llm | StrOutputParser()).with_listeners(on_end=self._save_context)

        # 5.call chain and get result
        chain_input = {"query": req.query.data}
        content = chain.invoke(chain_input, config={
            "configurable": {
                "mempry": memory,
            }
        })

        return success_json({"content": content})

    def ping(self):
        return {"ping": "pong"}
