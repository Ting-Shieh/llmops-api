#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/1/6 下午8:30
@Author : zsting29@gmail.com
@File   : assistant_agent_service.py
"""
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Generator
from uuid import UUID

from flask import current_app
from injector import inject
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool, tool
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from internal.core.agent.agents import AgentQueueManager, FunctionCallAgent
from internal.core.agent.entities.agent_entity import AgentConfig
from internal.core.agent.entities.queue_entity import QueueEvent
from internal.core.language_model.entities.model_entity import ModelFeature
from internal.core.language_model.providers.openai.chat import Chat
from internal.core.memory import TokenBufferMemory
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.model import Account, Message
from internal.schema.assistant_agent_schema import GetAssistantAgentMessagesWithPageReq, AssistantAgentChat
from internal.task.app_task import auto_create_app
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .conversation_service import ConversationService
from .faiss_service import FaissService


@inject
@dataclass
class AssistantAgentService(BaseService):
    """輔助智慧體服務"""
    db: SQLAlchemy
    faiss_service: FaissService
    conversation_service: ConversationService

    def chat(self, req: AssistantAgentChat, account: Account) -> Generator:
        """傳遞query與帳號實現與輔助Agent進行會話"""
        # 1.獲取輔助Agent對應的id
        assistant_agent_id = current_app.config.get("ASSISTANT_AGENT_ID")

        # 2.獲取當前應用的除錯會話資訊
        conversation = account.assistant_agent_conversation

        # 3.新建一條消息記錄
        message = self.create(
            Message,
            app_id=assistant_agent_id,
            conversation_id=conversation.id,
            invoke_from=InvokeFrom.ASSISTANT_AGENT,
            created_by=account.id,
            query=req.query.data,
            image_urls=req.image_urls.data,
            status=MessageStatus.NORMAL,
        )

        # 4.使用GPT模型作為輔助Agent的LLM大腦
        llm = Chat(
            model="gpt-4o-mini",
            temperature=0.8,
            features=[ModelFeature.TOOL_CALL, ModelFeature.AGENT_THOUGHT, ModelFeature.IMAGE_INPUT],
            metadata={},
        )

        # 5.實例化TokenBufferMemory用於提取短期記憶
        token_buffer_memory = TokenBufferMemory(
            db=self.db,
            conversation=conversation,
            model_instance=llm,
        )
        history = token_buffer_memory.get_history_prompt_messages(message_limit=3)

        # 6.將草稿配置中的tools轉換成LangChain工具
        tools = [
            self.faiss_service.convert_faiss_to_tool(),
            self.convert_create_app_to_tool(account.id),
        ]

        # 7.構建Agent智慧體，使用FunctionCallAgent
        agent = FunctionCallAgent(
            llm=llm,
            agent_config=AgentConfig(
                user_id=account.id,
                invoke_from=InvokeFrom.ASSISTANT_AGENT,
                enable_long_term_memory=True,
                tools=tools,
            ),
        )

        agent_thoughts = {}
        for agent_thought in agent.stream({
            "messages": [llm.convert_to_human_message(req.query.data, req.image_urls.data)],
            "history": history,
            "long_term_memory": conversation.summary,
        }):
            # 8.提取thought以及answer
            event_id = str(agent_thought.id)

            # 9.將數據填充到agent_thought，便於儲存到資料庫服務中
            if agent_thought.event != QueueEvent.PING:
                # 10.除了agent_message數據為疊加，其他均為覆蓋
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    if event_id not in agent_thoughts:
                        # 11.初始化智慧體消息事件
                        agent_thoughts[event_id] = agent_thought
                    else:
                        # 12.疊加智慧體消息
                        agent_thoughts[event_id] = agent_thoughts[event_id].model_copy(update={
                            "thought": agent_thoughts[event_id].thought + agent_thought.thought,
                            # 消息相關數據
                            "message": agent_thought.message,
                            "message_token_count": agent_thought.message_token_count,
                            "message_unit_price": agent_thought.message_unit_price,
                            "message_price_unit": agent_thought.message_price_unit,
                            # 答案相關欄位
                            "answer": agent_thoughts[event_id].answer + agent_thought.answer,
                            "answer_token_count": agent_thought.answer_token_count,
                            "answer_unit_price": agent_thought.answer_unit_price,
                            "answer_price_unit": agent_thought.answer_price_unit,
                            # Agent推理統計相關
                            "total_token_count": agent_thought.total_token_count,
                            "total_price": agent_thought.total_price,
                            "latency": agent_thought.latency,
                        })
                else:
                    # 13.處理其他類型事件的消息
                    agent_thoughts[event_id] = agent_thought
            data = {
                **agent_thought.model_dump(include={
                    "event", "thought", "observation", "tool", "tool_input", "answer", "latency",
                    "total_token_count",
                }),
                "id": event_id,
                "conversation_id": str(conversation.id),
                "message_id": str(message.id),
                "task_id": str(agent_thought.task_id),
            }
            yield f"event: {agent_thought.event}\ndata:{json.dumps(data)}\n\n"

        # 22.將消息以及推理過程添加到資料庫
        self.conversation_service.save_agent_thoughts(
            account_id=account.id,
            app_id=assistant_agent_id,
            app_config={"long_term_memory": {"enable": True}},
            conversation_id=conversation.id,
            message_id=message.id,
            agent_thoughts=[agent_thought for agent_thought in agent_thoughts.values()],
        )

    @classmethod
    def stop_chat(cls, task_id: UUID, account: Account) -> None:
        """根據傳遞的任務id+帳號停止某次響應會話"""
        AgentQueueManager.set_stop_flag(task_id, InvokeFrom.ASSISTANT_AGENT, account.id)

    def get_conversation_messages_with_page(
            self, req: GetAssistantAgentMessagesWithPageReq, account: Account
    ) -> tuple[list[Message], Paginator]:
        """根據傳遞的請求+帳號獲取與輔助Agent對話的消息分頁列表"""
        # 1.獲取應用的除錯會話
        conversation = account.assistant_agent_conversation

        # 2.構建分頁器並構建游標條件
        paginator = Paginator(db=self.db, req=req)
        filters = []
        if req.created_at.data:
            # 3.將時間戳轉換成DateTime
            created_at_datetime = datetime.fromtimestamp(req.created_at.data)
            filters.append(Message.created_at <= created_at_datetime)

        # 4.執行分頁並查詢數據
        messages = paginator.paginate(
            self.db.session.query(Message).options(joinedload(Message.agent_thoughts)).filter(
                Message.conversation_id == conversation.id,
                Message.status.in_([MessageStatus.STOP, MessageStatus.NORMAL]),
                Message.answer != "",
                *filters,
            ).order_by(desc("created_at"))
        )

        return messages, paginator

    def delete_conversation(self, account: Account) -> None:
        """根據傳遞的帳號，清空輔助Agent智慧體會話消息列表"""
        self.update(account, assistant_agent_conversation_id=None)

    @classmethod
    def convert_create_app_to_tool(cls, account_id: UUID) -> BaseTool:
        """定義自動創建Agent應用LangChain工具"""

        class CreateAppInput(BaseModel):
            """創建Agent/應用輸入結構"""
            name: str = Field(description="需要創建的Agent/應用名稱，長度不超過50個字元")
            description: str = Field(description="需要創建的Agent/應用描述，請詳細概括該應用的功能")

        @tool("create_app", args_schema=CreateAppInput)
        def create_app(name: str, description: str) -> str:
            """如果用戶提出了需要創建一個Agent/應用，你可以調用此工具，參數的輸入是應用的名稱+描述，返回的數據是創建後的成功提示"""
            # 1.調用celery非同步任務在後端創建應用
            auto_create_app.delay(name, description, account_id)

            # 2.返回成功提示
            return f"已調用後端非同步任務創建Agent應用。\n應用名稱: {name}\n應用描述: {description}"

        return create_app
