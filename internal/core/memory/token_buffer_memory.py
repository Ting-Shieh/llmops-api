#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/26 下午4:00
@Author : zsting29@gmail.com
@File   : token_buffer_memory.py
"""
from dataclasses import dataclass

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AnyMessage, AIMessage, trim_messages, get_buffer_string
from sqlalchemy import desc

from internal.entity.conversation_entity import MessageStatus
from internal.model import Conversation, Message
from pkg.sqlalchemy import SQLAlchemy


@dataclass
class TokenBufferMemory:
    """基於token計數的緩衝記憶組件"""
    db: SQLAlchemy  # 資料庫實例
    conversation: Conversation  # 會話模型
    model_instance: BaseLanguageModel  # LLM大語言模型

    def get_history_prompt_messages(
            self,
            max_token_limit: int = 2000,
            message_limit: int = 10,
    ) -> list[AnyMessage]:
        """根據傳遞的token限制+消息條數限制獲取指定會話模型的歷史消息列表"""
        # 1.判斷會話模型是否存在，如果不存在則直接返回空列表
        if self.conversation is None:
            return []

        # 2.查詢該會話的消息列表，並且使用時間進行倒序，同時匹配答案不為空、匹配會話id、沒有軟刪除、狀態是正常
        messages = self.db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            Message.answer != "",
            Message.is_deleted == False,
            Message.status.in_([
                MessageStatus.NORMAL,
                MessageStatus.STOP,
                MessageStatus.TIMEOUT
            ]),
        ).order_by(desc("created_at")).limit(message_limit).all()
        messages = list(reversed(messages))

        # 3.將messages轉換成LangChain消息列表
        prompt_messages = []
        for message in messages:
            prompt_messages.extend([
                self.model_instance.convert_to_human_message(message.query, message.image_urls),
                AIMessage(content=message.answer),
            ])

        # 4.調用LangChain繼承的trim_messages函數剪切消息列表
        return trim_messages(
            messages=prompt_messages,
            max_tokens=max_token_limit,
            token_counter=self.model_instance,
            strategy="last",
            start_on="human",
            end_on="ai",
        )

    def get_history_prompt_text(
            self,
            human_prefix: str = "Human",
            ai_prefix: str = "AI",
            max_token_limit: int = 2000,
            message_limit: int = 10,
    ) -> str:
        """根據傳遞的數據獲取指定會話歷史消息提示文本(短期記憶的文本形式，用於文本生成模型)"""
        # 1.根據傳遞的資訊獲取歷史消息列表
        messages = self.get_history_prompt_messages(max_token_limit, message_limit)

        # 2.調用LangChain集成的get_buffer_string()函數將消息列錶轉換成文本
        return get_buffer_string(messages, human_prefix, ai_prefix)
