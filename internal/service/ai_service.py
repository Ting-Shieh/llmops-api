#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/2 下午6:50
@Author : zsting29@gmail.com
@File   : ai_service.py
"""
import json
from dataclasses import dataclass
from typing import Generator
from uuid import UUID

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.ai_entity import OPTIMIZE_PROMPT_TEMPLATE
from internal.exception import ForbiddenException
from internal.model import Account, Message
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .conversation_service import ConversationService


@inject
@dataclass
class AIService(BaseService):
    """AI服務"""
    db: SQLAlchemy
    conversation_service: ConversationService

    def generate_suggested_questions_from_message_id(self, message_id: UUID, account: Account) -> list[str]:
        """根據傳遞的消息id+帳號生成建議問題列表"""
        # 1.查詢消息並校驗權限資訊
        message = self.get(Message, message_id)
        if not message or message.created_by != account.id:
            raise ForbiddenException("該條消息不存在或無權限")

        # 2.構建對話歷史列表
        histories = f"Human: {message.query}\nAI: {message.answer}"

        # 3.調用服務生成建議問題
        return self.conversation_service.generate_suggested_questions(histories)

    @classmethod
    def optimize_prompt(cls, prompt: str) -> Generator[str, None, None]:
        """根據傳遞的prompt進行最佳化生成"""
        # 1.構建最佳化prompt的提示詞模板
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", OPTIMIZE_PROMPT_TEMPLATE),
            ("human", "{prompt}")
        ])

        # 2.構建LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

        # 3.組裝最佳化鏈
        optimize_chain = prompt_template | llm | StrOutputParser()

        # 4.調用鏈並流式事件返回
        for optimize_prompt in optimize_chain.stream({"prompt": prompt}):
            # 5.組裝響應數據
            data = {"optimize_prompt": optimize_prompt}
            yield f"event: optimize_prompt\ndata: {json.dumps(data)}\n\n"
