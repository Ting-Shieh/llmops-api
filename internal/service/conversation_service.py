#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/20 下午10:35
@Author : zsting29@gmail.com
@File   : conversation_service.py
"""
import logging
from dataclasses import dataclass
from threading import Thread
from typing import Any
from uuid import UUID

from flask import Flask, current_app
from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.conversation_entity import (
    SUMMARIZER_TEMPLATE,
    CONVERSATION_NAME_TEMPLATE,
    ConversationInfo,
    SUGGESTED_QUESTIONS_TEMPLATE,
    SuggestedQuestions, InvokeFrom,
)
from internal.exception import NotFoundException
from internal.model import Conversation, Message, MessageAgentThought, Account
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..core.agent.entities.queue_entity import QueueEvent, AgentThought


@inject
@dataclass
class ConversationService(BaseService):
    """會話服務"""
    db: SQLAlchemy

    @classmethod
    def summary(cls, human_message: str, ai_message: str, old_summary: str = "") -> str:
        """根據傳遞的人類消息、AI消息還有原始的摘要資訊總結生成一段新的摘要"""
        # 1.創建prompt
        prompt = ChatPromptTemplate.from_template(SUMMARIZER_TEMPLATE)

        # 2.構建大語言模型實例，並且將大語言模型的溫度調低，降低幻覺的機率
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

        # 3.構建鏈應用
        summary_chain = prompt | llm | StrOutputParser()

        # 4.調用鏈並獲取新摘要資訊
        new_summary = summary_chain.invoke({
            "summary": old_summary,
            "new_lines": f"Human: {human_message}\nAI: {ai_message}",
        })

        return new_summary

    @classmethod
    def generate_conversation_name(cls, query: str) -> str:
        """根據傳遞的query生成對應的會話名字，並且語言與用戶的輸入保持一致"""
        # 1.創建prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", CONVERSATION_NAME_TEMPLATE),
            ("human", "{query}")
        ])

        # 2.構建大語言模型實例，並且將大語言模型的溫度調低，降低幻覺的機率
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        structured_llm = llm.with_structured_output(ConversationInfo)

        # 3.構建鏈應用
        chain = prompt | structured_llm

        # 4.提取並整理query，截取長度過長的部分
        if len(query) > 2000:
            query = query[:300] + "...[TRUNCATED]..." + query[-300:]
        query = query.replace("\n", " ")

        # 5.調用鏈並獲取會話資訊
        conversation_info = chain.invoke({"query": query})

        # 6.提取會話名稱
        name = "新的會話"
        try:
            if conversation_info and hasattr(conversation_info, "subject"):
                name = conversation_info.subject
        except Exception as e:
            logging.exception(
                "提取會話名稱出錯, conversation_info: %(conversation_info)s, 錯誤資訊: %(error)s",
                {"conversation_info": conversation_info, "error": e},
            )
        if len(name) > 75:
            name = name[:75] + "..."

        return name

    @classmethod
    def generate_suggested_questions(cls, histories: str) -> list[str]:
        """根據傳遞的歷史資訊生成最多不超過3個的建議問題"""
        # 1.創建prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SUGGESTED_QUESTIONS_TEMPLATE),
            ("human", "{histories}")
        ])

        # 2.構建大語言模型實例，並且將大語言模型的溫度調低，降低幻覺的機率
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        structured_llm = llm.with_structured_output(SuggestedQuestions)

        # 3.構建鏈應用
        chain = prompt | structured_llm

        # 4.調用鏈並獲取建議問題列表
        suggested_questions = chain.invoke({"histories": histories})

        # 5.提取建議問題列表
        questions = []
        try:
            if suggested_questions and hasattr(suggested_questions, "questions"):
                questions = suggested_questions.questions
        except Exception as e:
            logging.exception(
                "生成建議問題出錯, suggested_questions: %(suggested_questions)s, 錯誤資訊: %(error)s",
                {"suggested_questions": suggested_questions, "error": e},
            )
        if len(questions) > 3:
            questions = questions[:3]

        return questions

    def save_agent_thoughts(
            self,
            account_id: UUID,
            app_id: UUID,
            app_config: dict[str, Any],
            conversation_id: UUID,
            message_id: UUID,
            agent_thoughts: list[AgentThought],
    ):
        """儲存智慧體推理步驟消息"""
        # 1.定義變數儲存推理位置及總耗時
        position = 0
        latency = 0

        # 2.在子執行緒中重新查詢conversation以及message，確保對象會被子執行緒的會話管理到
        conversation = self.get(Conversation, conversation_id)
        message = self.get(Message, message_id)

        # 3.循環遍歷所有的智慧體推理過程執行儲存操作
        for agent_thought in agent_thoughts:
            # 4.儲存長期記憶召回、推理、消息、動作、知識庫檢索等步驟
            if agent_thought.event in [
                QueueEvent.LONG_TERM_MEMORY_RECALL,
                QueueEvent.AGENT_THOUGHT,
                QueueEvent.AGENT_MESSAGE,
                QueueEvent.AGENT_ACTION,
                QueueEvent.DATASET_RETRIEVAL,
            ]:
                # 5.更新位置及總耗時
                position += 1
                latency += agent_thought.latency

                # 6.創建智慧體消息推理步驟
                self.create(
                    MessageAgentThought,
                    app_id=app_id,
                    conversation_id=conversation.id,
                    message_id=message.id,
                    invoke_from=InvokeFrom.DEBUGGER,
                    created_by=account_id,
                    position=position,
                    event=agent_thought.event,
                    thought=agent_thought.thought,
                    observation=agent_thought.observation,
                    tool=agent_thought.tool,
                    tool_input=agent_thought.tool_input,
                    # 消息相關數據
                    message=agent_thought.message,
                    message_token_count=agent_thought.message_token_count,
                    message_unit_price=agent_thought.message_unit_price,
                    message_price_unit=agent_thought.message_price_unit,
                    # 答案相關欄位
                    answer=agent_thought.answer,
                    answer_token_count=agent_thought.answer_token_count,
                    answer_unit_price=agent_thought.answer_unit_price,
                    answer_price_unit=agent_thought.answer_price_unit,
                    # Agent推理統計相關
                    total_token_count=agent_thought.total_token_count,
                    total_price=agent_thought.total_price,
                    latency=agent_thought.latency,
                )

            # 7.檢測事件是否為Agent_message
            if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                # 8.更新消息資訊
                self.update(
                    message,
                    # 消息相關欄位
                    message=agent_thought.message,
                    message_token_count=agent_thought.message_token_count,
                    message_unit_price=agent_thought.message_unit_price,
                    message_price_unit=agent_thought.message_price_unit,
                    # 答案相關欄位
                    answer=agent_thought.answer,
                    answer_token_count=agent_thought.answer_token_count,
                    answer_unit_price=agent_thought.answer_unit_price,
                    answer_price_unit=agent_thought.answer_price_unit,
                    # Agent推理統計相關
                    total_token_count=agent_thought.total_token_count,
                    total_price=agent_thought.total_price,
                    latency=latency,
                )

                # 9.檢測是否開啟長期記憶
                if app_config["long_term_memory"]["enable"]:
                    Thread(
                        target=self._generate_summary_and_update,
                        kwargs={
                            "flask_app": current_app._get_current_object(),
                            "conversation_id": conversation.id,
                            "query": message.query,
                            "answer": agent_thought.answer,
                        },
                    ).start()

                # 10.處理生成新會話名稱
                if conversation.is_new:
                    Thread(
                        target=self._generate_conversation_name_and_update,
                        kwargs={
                            "flask_app": current_app._get_current_object(),
                            "conversation_id": conversation.id,
                            "query": message.query,
                        }
                    ).start()

            # 11.判斷是否為停止或者錯誤，如果是則需要更新消息狀態
            if agent_thought.event in [QueueEvent.TIMEOUT, QueueEvent.STOP, QueueEvent.ERROR]:
                self.update(
                    message,
                    status=agent_thought.event,
                    error=agent_thought.observation,
                )
                break

    def _generate_summary_and_update(
            self,
            flask_app: Flask,
            conversation_id: UUID,
            query: str,
            answer: str,
    ):
        with flask_app.app_context():
            # 1.根據id獲取會話
            conversation = self.get(Conversation, conversation_id)

            # 2.計算會話新摘要資訊
            new_summary = self.summary(
                query,
                answer,
                conversation.summary
            )

            # 3.更新會話的摘要資訊
            self.update(
                conversation,
                summary=new_summary,
            )

    def _generate_conversation_name_and_update(
            self,
            flask_app: Flask,
            conversation_id: UUID,
            query: str
    ) -> None:
        """生成會話名字並更新"""
        with flask_app.app_context():
            # 1.根據會話id獲取會話
            conversation = self.get(Conversation, conversation_id)

            # 2.計算獲取新會話名字
            new_conversation_name = self.generate_conversation_name(query)

            # 3.調用更新服務更新會話名稱
            self.update(
                conversation,
                name=new_conversation_name,
            )

    def get_conversation(
            self,
            conversation_id: UUID,
            account: Account
    ) -> Conversation:
        """根據傳遞的會話id+account，獲取指定的會話資訊"""
        # 1.根據conversation_id查詢會話記錄
        conversation = self.get(Conversation, conversation_id)
        if (
                not conversation
                or conversation.created_by != account.id
                or conversation.is_deleted
        ):
            raise NotFoundException("該會話不存在或被刪除，請核實後重試")

        # 2.校驗通過返回會話
        return conversation
