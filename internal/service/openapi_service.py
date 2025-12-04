#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/26 下午11:40
@Author : zsting29@gmail.com
@File   : openapi_service.py
"""
import json
from dataclasses import dataclass
from typing import Generator

from flask import current_app
from injector import inject

from internal.core.agent.agents import FunctionCallAgent, ReACTAgent
from internal.core.agent.entities.agent_entity import AgentConfig
from internal.core.agent.entities.queue_entity import QueueEvent
from internal.core.language_model.entities.model_entity import ModelFeature
from internal.core.memory import TokenBufferMemory
from internal.entity.app_entity import AppStatus
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.entity.dataset_entity import RetrievalSource
from internal.exception import NotFoundException, ForbiddenException
from internal.model import Account, EndUser, Conversation, Message
from internal.schema.openapi_schema import OpenAPIChatReq
from pkg.response import Response
from pkg.sqlalchemy import SQLAlchemy
from .app_config_service import AppConfigService
from .app_service import AppService
from .base_service import BaseService
from .conversation_service import ConversationService
from .language_model_service import LanguageModelService
from .retrieval_service import RetrievalService


@inject
@dataclass
class OpenAPIService(BaseService):
    """開放API服務"""
    db: SQLAlchemy
    app_service: AppService
    retrieval_service: RetrievalService
    app_config_service: AppConfigService
    conversation_service: ConversationService
    language_model_service: LanguageModelService

    def chat(self, req: OpenAPIChatReq, account: Account):
        """根據傳遞的請求+帳號資訊發起聊天對話，返回數據為塊內容或者生成器"""
        # 1.判斷當前應用是否屬於當前帳號
        app = self.app_service.get_app(req.app_id.data, account)

        # 2.判斷當前應用是否已發布
        if app.status != AppStatus.PUBLISHED:
            raise NotFoundException("該應用不存在或未發布，請核實後重試")

        # 3.判斷是否傳遞了終端用戶id，如果傳遞了則檢測終端用戶關聯的應用
        if req.end_user_id.data:
            end_user = self.get(EndUser, req.end_user_id.data)
            if not end_user or end_user.app_id != app.id:
                raise ForbiddenException("當前帳號不存在或不屬於該應用，請核實後重試")
        else:
            # 4.如果不存在則創建一個終端用戶
            end_user = self.create(
                EndUser,
                **{"tenant_id": account.id, "app_id": app.id},
            )

        # 5.檢測是否傳遞了會話id，如果傳遞了需要檢測會話的歸屬資訊
        if req.conversation_id.data:
            conversation = self.get(Conversation, req.conversation_id.data)
            if (
                    not conversation
                    or conversation.app_id != app.id
                    or conversation.invoke_from != InvokeFrom.SERVICE_API
                    or conversation.created_by != end_user.id
            ):
                raise ForbiddenException("該會話不存在，或者不屬於該應用/終端用戶/調用方式")
        else:
            # 6.如果不存在則創建會話資訊
            conversation = self.create(Conversation, **{
                "app_id": app.id,
                "name": "New Conversation",
                "invoke_from": InvokeFrom.SERVICE_API,
                "created_by": end_user.id,
            })

        # 7.獲取校驗後的運行時配置
        app_config = self.app_config_service.get_app_config(app)

        # 8.新建一條消息記錄
        message = self.create(Message, **{
            "app_id": app.id,
            "conversation_id": conversation.id,
            "invoke_from": InvokeFrom.SERVICE_API,
            "created_by": end_user.id,
            "query": req.query.data,
            "image_urls": req.image_urls.data,
            "status": MessageStatus.NORMAL,
        })

        # 9.從語言模型中根據模型配置獲取模型實例
        llm = self.language_model_service.load_language_model(app_config.get("model_config", {}))

        # 10.實例化TokenBufferMemory用於提取短期記憶
        token_buffer_memory = TokenBufferMemory(
            db=self.db,
            conversation=conversation,
            model_instance=llm,
        )
        history = token_buffer_memory.get_history_prompt_messages(
            message_limit=app_config["dialog_round"],
        )

        # 11.將草稿配置中的tools轉換成LangChain工具
        tools = self.app_config_service.get_langchain_tools_by_tools_config(app_config["tools"])

        # 12.檢測是否關聯了知識庫
        if app_config["datasets"]:
            # 13.構建LangChain知識庫檢索工具
            dataset_retrieval = self.retrieval_service.create_langchain_tool_from_search(
                flask_app=current_app._get_current_object(),
                dataset_ids=[dataset["id"] for dataset in app_config["datasets"]],
                account_id=account.id,
                retrival_source=RetrievalSource.APP,
                **app_config["retrieval_config"],
            )
            tools.append(dataset_retrieval)

        # 14.檢測是否關聯工作流，如果關聯了工作流則將工作流構建成工具添加到tools中
        if app_config["workflows"]:
            workflow_tools = self.app_config_service.get_langchain_tools_by_workflow_ids(
                [workflow["id"] for workflow in app_config["workflows"]]
            )
            tools.extend(workflow_tools)

        # 14.根據LLM是否支持tool_call決定使用不同的Agent
        agent_class = FunctionCallAgent if ModelFeature.TOOL_CALL in llm.features else ReACTAgent
        agent = agent_class(
            llm=llm,
            agent_config=AgentConfig(
                user_id=account.id,
                invoke_from=InvokeFrom.DEBUGGER,
                preset_prompt=app_config["preset_prompt"],
                enable_long_term_memory=app_config["long_term_memory"]["enable"],
                tools=tools,
                review_config=app_config["review_config"],
            ),
        )

        # 15.定義智慧體狀態基礎數據
        agent_state = {
            "messages": [llm.convert_to_human_message(req.query.data, req.image_urls.data)],
            "history": history,
            "long_term_memory": conversation.summary,
        }

        # 16.根據stream類型差異執行不同的代碼
        if req.stream.data is True:
            agent_thoughts_dict = {}

            def handle_stream() -> Generator:
                """流式事件處理器，在Python只要在函數內部使用了yield關鍵字，那麼這個函數的返回值類型肯定是生成器"""
                for agent_thought in agent.stream(agent_state):
                    # 提取thought以及answer
                    event_id = str(agent_thought.id)

                    # 將數據填充到agent_thought，便於儲存到資料庫服務中
                    if agent_thought.event != QueueEvent.PING:
                        # 除了agent_message數據為疊加，其他均為覆蓋
                        if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                            if event_id not in agent_thoughts_dict:
                                # 初始化智慧體消息事件
                                agent_thoughts_dict[event_id] = agent_thought
                            else:
                                # 疊加智慧體消息
                                agent_thoughts_dict[event_id] = agent_thoughts_dict[event_id].model_copy(update={
                                    "thought": agent_thoughts_dict[event_id].thought + agent_thought.thought,
                                    "answer": agent_thoughts_dict[event_id].answer + agent_thought.answer,
                                    "latency": agent_thought.latency,
                                })
                        else:
                            # 處理其他類型事件的消息
                            agent_thoughts_dict[event_id] = agent_thought
                    data = {
                        **agent_thought.dict(include={
                            "event", "thought", "observation", "tool", "tool_input", "answer", "latency",
                        }),
                        "id": event_id,
                        "end_user_id": str(end_user.id),
                        "conversation_id": str(conversation.id),
                        "message_id": str(message.id),
                        "task_id": str(agent_thought.task_id),
                    }
                    yield f"event: {agent_thought.event}\ndata:{json.dumps(data)}\n\n"

                # 22.將消息以及推理過程添加到資料庫
                self.conversation_service.save_agent_thoughts(
                    account_id=account.id,
                    app_id=app.id,
                    app_config=app_config,
                    conversation_id=conversation.id,
                    message_id=message.id,
                    agent_thoughts=[agent_thought for agent_thought in agent_thoughts_dict.values()],
                )

            return handle_stream()

        # 17.塊內容輸出
        agent_result = agent.invoke(agent_state)

        # 18.將消息以及推理過程添加到資料庫
        self.conversation_service.save_agent_thoughts(
            account_id=account.id,
            app_id=app.id,
            app_config=app_config,
            conversation_id=conversation.id,
            message_id=message.id,
            agent_thoughts=agent_result.agent_thoughts,
        )

        return Response(data={
            "id": str(message.id),
            "end_user_id": str(end_user.id),
            "conversation_id": str(conversation.id),
            "query": req.query.data,
            "image_urls": req.image_urls.data,
            "answer": agent_result.answer,
            "total_token_count": 0,
            "latency": agent_result.latency,
            "agent_thoughts": [{
                "id": str(agent_thought.id),
                "event": agent_thought.event,
                "thought": agent_thought.thought,
                "observation": agent_thought.observation,
                "tool": agent_thought.tool,
                "tool_input": agent_thought.tool_input,
                "latency": agent_thought.latency,
                "created_at": 0,
            } for agent_thought in agent_result.agent_thoughts]
        })
