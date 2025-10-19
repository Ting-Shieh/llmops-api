#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午2:30
@Author : zsting29@gmail.com
@File   : app_handler.py
"""
import json
from dataclasses import dataclass
from operator import itemgetter
from queue import Queue
from threading import Thread
from typing import Dict, Any, Literal, Generator
from uuid import UUID, uuid4

from flask_login import login_required, current_user
from injector import inject
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.memory import BaseMemory
from langchain_core.messages import ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from langgraph.constants import END
from langgraph.graph import MessagesState, StateGraph

from internal.core.tools.buildin_tools.providers import BuildinProviderManager
from internal.schema.app_schema import CompletionReq, CreateAppReq, UpdateAppReq, GetAppResp
from internal.service import (
    AppService,
    VectorDatabaseService,
    ApiToolService,
    ConversationService
)
from pkg.response import (
    success_json,
    validate_error_json,
    success_message,
    compact_generate_response
)


@inject
@dataclass
class AppHandler:
    """應用控制器"""
    app_service: AppService
    vector_database_service: VectorDatabaseService
    buildin_provider_manager: BuildinProviderManager
    api_tool_service: ApiToolService
    conversation_service: ConversationService

    @login_required
    def create_app(self):
        """調用服務創建新的App紀錄"""
        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)
        app = self.app_service.create_app(req, current_user)
        return success_message(f"應用已經成功創建，id為{app.id}")

    @login_required
    def get_app(self, app_id: UUID):
        """獲取指定的應用基礎資訊"""
        app = self.app_service.get_app(app_id, current_user)
        resp = GetAppResp()
        return success_json(resp.dump(app))

    @login_required
    def update_app(self, app_id: UUID):
        """根據傳遞的資訊更新指定的應用"""
        # 1.提取數據並校驗
        req = UpdateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新數據
        self.app_service.update_app(app_id, current_user, **req.data)

        return success_message("修改Agent智慧體應用成功")

    @login_required
    def delete_app(self, app_id: UUID):
        """根據傳遞的資訊刪除指定的應用"""
        self.app_service.delete_app(app_id, current_user)
        return success_message("刪除Agent智慧體應用成功")

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

    def debug(self, app_id: UUID):
        # 1.獲取接口的參數
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        q = Queue()
        query = req.query.data

        def graph_app() -> None:
            """Create Graph圖程序應用並執行"""
            # tools工具列表
            tools = [
                self.buildin_provider_manager.get_tool("google", "google_serper")(),
                self.buildin_provider_manager.get_tool("google", "google_weather")(),
                self.buildin_provider_manager.get_tool("dalle", "dalle3")()
            ]

            # 定義大語言模型/聊天機器人節點
            def chatbot(state: MessagesState) -> MessagesState:
                """聊天機器人"""
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.7
                ).bind_tools(tools)

                is_first_chunk = True
                is_tool_call = False
                gathered = None
                id = str(uuid4())
                for chunk in llm.stream(state["messages"]):
                    if is_first_chunk and chunk.content == "" and not chunk.tool_calls:
                        continue

                    if is_first_chunk:
                        gathered = chunk
                        is_first_chunk = False
                    else:
                        gathered += chunk

                    if chunk.tool_calls or is_tool_call:
                        is_tool_call = True
                        q.put({
                            "id": id,
                            "event": "agent_thought",
                            "data": json.dumps(chunk.tool_call_chunks)
                        })
                    else:
                        q.put({
                            "id": id,
                            "event": "agent_message",
                            "data": chunk.content
                        })
                return {"messages": [gathered]}

            def tool_executor(state: MessagesState) -> MessagesState:
                tool_calls = state["messages"][-1].tool_calls

                tools_by_name = {
                    tool.name: tool for tool in tools
                }

                messages = []
                for tool_call in tool_calls:
                    id = str(uuid4())
                    tool = tools_by_name[tool_call["name"]]
                    tool_result = tool.invoke(tool_call["args"])
                    messages.append(ToolMessage(
                        tool_call_id=tool_call['id'],
                        content=json.dumps(tool_result),
                        name=tool_call["name"]
                    ))

                    q.put({
                        "id": id,
                        "event": "agent_action",
                        "data": json.dumps(tool_result)
                    })
                return {"messages": messages}

            def route(state: MessagesState) -> Literal["tool_executor", "__end__"]:
                ai_message = state["messages"][-1]
                if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
                    return "tool_executor"
                return END

            graph_builder = StateGraph(MessagesState)

            graph_builder.add_node("llm", chatbot)
            graph_builder.add_node("tool_executor", tool_executor)

            graph_builder.set_entry_point("llm")
            graph_builder.add_conditional_edges("llm", route)
            graph_builder.add_edge("tool_executor", "llm")

            graph = graph_builder.compile()
            result = graph.invoke({"messages": [("human", query)]})

            print("Final Result:", result)
            q.put(None)

        def stream_event_response() -> Generator:
            while True:
                item = q.get()
                if item is None:
                    break
                yield f"event: {item.get("event")}\ndata:{json.dumps(item)}\n\n"
                q.task_done()

        t = Thread(target=graph_app)
        t.start()

        return compact_generate_response(stream_event_response())

    def _debug(self, app_id: UUID):
        """聊天接口"""
        # 1.獲取接口的參數
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.創建prompt與記憶
        system_prompt = "你是一個強大的聊天機器人，能依據對應的上下文和歷史對話訊息回覆用戶問題 \n\n<context>{context}</context>"
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{query}"),
        ])
        # print(os.getcwd())
        # print(os.path.abspath('.'))
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
        retriever = self.vector_database_service.get_retriever() | self.vector_database_service.combine_documents
        chain = (RunnablePassthrough.assign(
            history=RunnableLambda(self._load_memory_variable) | itemgetter("history"),
            context=itemgetter("query") | retriever
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
        conversation_name = self.conversation_service.generate_conversation_name("我喜歡作詞作曲")
        return success_json({"conversation_name": conversation_name})

        # google_serper = self.buildin_provider_manager.get_tool(provider_name="google", tool_name="google_serper")()
        # print(google_serper)
        # print(google_serper.invoke("今天台積電最高股價是多少？"))

        # google = self.buildin_provider_manager.get_provider("google")
        # google_serper_entity = google.get_tool_entity("google_serper")
        # print(google_serper_entity)

        # 獲取所有服務提供商
        # providers = self.buildin_provider_manager.get_provider＿entities()
        #
        # return success_json({"providers": [provider.dict() for provider in providers]})
        # demo_task.delay(uuid.uuid4())
        # return self.api_tool_service.api_tool_invoke()

        # return {"ping": "pong"}
