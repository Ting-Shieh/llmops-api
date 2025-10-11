#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/20 下午11:16
@Author : zsting29@gmail.com
@File   : conversation.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    DateTime,
    Boolean,
    text,
    func,
    PrimaryKeyConstraint, Float, Numeric, Integer,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from internal.extension.database_extension import db


class Conversation(db.Model):
    """交流會話模型"""
    __tablename__ = "conversation"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_conversation_id"),
        # Index("conversation_app_id_idx", "app_id"),
        # Index("conversation_app_created_by_idx", "created_by"),
    )

    id = Column(
        UUID,
        nullable=False,
        server_default=text("uuid_generate_v4()")
    )
    app_id = Column(
        UUID,
        nullable=False
    )  # 關聯應用id
    name = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )  # 會話名稱
    summary = Column(
        Text,
        nullable=False,
        server_default=text("''::text")
    )  # 會話摘要/長期記憶
    is_pinned = Column(
        Boolean,
        nullable=False,
        server_default=text("false")
    )  # 是否置頂
    is_deleted = Column(
        Boolean,
        nullable=False,
        server_default=text("false")
    )  # 是否刪除
    invoke_from = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )  # 調用來源
    created_by = Column(
        UUID,
        nullable=True,
    )  # 會話創建者，會隨著invoke_from的差異記錄不同的資訊，其中web_app和debugger會記錄帳號id、service_api會記錄終端用戶id
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))

    @property
    def is_new(self) -> bool:
        """只读属性，用于判断该会话是否是第一次创建"""
        message_count = db.session.query(func.count(Message.id)).filter(
            Message.conversation_id == self.id,
        ).scalar()

        return False if message_count > 1 else True


class Message(db.Model):
    """交流消息模型"""
    __tablename__ = "message"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_message_id"),
        # Index("message_conversation_id_idx", "conversation_id"),
        # Index("message_created_by_idx", "created_by"),
    )

    id = Column(
        UUID,
        nullable=False,
        server_default=text("uuid_generate_v4()")
    )

    # 消息關聯的紀錄
    app_id = Column(
        UUID,
        nullable=False
    )  # 關聯應用id
    conversation_id = Column(
        UUID,
        nullable=False
    )  # 關聯會話id
    invoke_from = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying"),
    )  # 調用來源，涵蓋service_api、web_app、debugger等
    created_by = Column(
        UUID,
        nullable=False
    )  # 消息的創建來源，有可能是LLMOps的用戶，也有可能是開放API的終端用戶

    # 消息關聯的原始問題
    query = Column(
        Text,
        nullable=False,
        server_default=text("''::text")
    )  # 用戶提問的原始query
    image_urls = Column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb")
    )  # 用戶提問的圖片URL列表資訊
    message = Column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb")
    )  # 產生answer的消息列表
    message_token_count = Column(
        Integer,
        nullable=False,
        server_default=text("0")
    )  # 消息列表的token總數
    message_unit_price = Column(
        Numeric(10, 7),
        nullable=False,
        server_default=text("0.0")
    )  # 消息的單價
    message_price_unit = Column(
        Numeric(10, 4),
        nullable=False,
        server_default=text("0.0")
    )  # 消息的價格單位

    # 消息關聯的答案資訊
    answer = Column(
        Text,
        nullable=False,
        server_default=text("''::text")
    )  # Agent生成的消息答案
    answer_token_count = Column(
        Integer,
        nullable=False,
        server_default=text("0")
    )  # 消息答案的token數
    answer_unit_price = Column(
        Numeric(10, 7),
        nullable=False,
        server_default=text("0.0")
    )  # token的單位價格
    answer_price_unit = Column(
        Numeric(10, 4),
        nullable=False,
        server_default=text("0.0")
    )  # token的價格單位

    # 消息的相關統計資訊
    latency = Column(
        Float,
        nullable=False,
        server_default=text("0.0")
    )  # 消息的總耗時
    is_deleted = Column(
        Boolean,
        nullable=False,
        server_default=text("false")
    )  # 軟刪除標記
    status = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )  # 消息的狀態，涵蓋正常、錯誤、停止
    error = Column(
        Text,
        nullable=False,
        server_default=text("''::text")
    )  # 發生錯誤時記錄的資訊
    total_token_count = Column(
        Integer,
        nullable=False,
        server_default=text("0")
    )  # 消耗的總token數，計算步驟的消耗
    total_price = Column(
        Numeric(10, 7),
        nullable=False,
        server_default=text("0.0")
    )  # 消耗的總價格，計算步驟的總消耗

    # 消息時間相關資訊
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)')
    )

    # 智慧體推理列表，創建表關聯
    agent_thoughts = relationship(
        "MessageAgentThought",
        backref="msg",
        lazy="selectin",
        passive_deletes="all",
        uselist=True,
        foreign_keys=[id],
        primaryjoin="MessageAgentThought.message_id == Message.id",
    )

    @property
    def conversation(self) -> Conversation:
        """只讀屬性，返回該消息對應的會話記錄"""
        return db.session.query(Conversation).get(self.conversation_id)


class MessageAgentThought(db.Model):
    """智慧體消息推理模型，用於記錄Agent生成最終消息答案時"""
    __tablename__ = "message_agent_thought"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_message_agent_thought_id"),
        # Index("message_agent_thought_app_id_idx", "app_id"),
        # Index("message_agent_thought_conversation_id_idx", "conversation_id"),
        # Index("message_agent_thought_message_id_idx", "message_id"),
    )

    id = Column(
        UUID,
        nullable=False,
        server_default=text("uuid_generate_v4()")
    )

    # 推理步驟關聯資訊
    app_id = Column(UUID, nullable=False)  # 關聯的應用id
    conversation_id = Column(UUID, nullable=False)  # 關聯的會話id
    message_id = Column(UUID, nullable=False)  # 關聯的消息id
    invoke_from = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying"),
    )  # 調用來源，涵蓋service_api、web_app、debugger等
    created_by = Column(
        UUID,
        nullable=False
    )  # 消息的創建來源，有可能是LLMOps的用戶，也有可能是開放API的終端用戶

    # 該步驟在消息中執行的位置
    position = Column(
        Integer,
        nullable=False,
        server_default=text("0")
    )  # 推理觀察的位置

    # 推理與觀察，分別記錄LLM和非LLM產生的消息
    event = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )  # 事件名稱
    thought = Column(
        Text,
        nullable=False,
        server_default=text("''::text")
    )  # 推理內容(儲存LLM生成的內容)
    observation = Column(
        Text,
        nullable=False,
        server_default=text("''::text")
    )  # 觀察內容(儲存知識庫、工具等非LLM生成的內容，用於讓LLM觀察)

    # 工具相關，涵蓋工具名稱、輸入，在調用工具時會生成
    tool = Column(
        Text,
        nullable=False,
        server_default=text("''::text")
    )  # 調用工具名稱
    tool_input = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )  # LLM調用工具的輸入，如果沒有則為空字典

    # Agent推理觀察步驟使用的消息列表(傳遞prompt消息內容)
    message = Column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb")
    )  # 該步驟調用LLM使用的提示消息
    message_token_count = Column(
        Integer,
        nullable=False,
        server_default=text("0")
    )  # 消息花費的token數
    message_unit_price = Column(
        Numeric(10, 7),
        nullable=False,
        server_default=text("0.0")
    )  # 單價，所有LLM的計算方式統一為CNY
    message_price_unit = Column(
        Numeric(10, 4),
        nullable=False,
        server_default=text("0"),
    )  # 價格單位，值為1000代表1000token對應的單價

    # LLM生成内容相关(生成内容)
    answer = Column(
        Text,
        nullable=False,
        server_default=text("''::text")
    )  # LLM生成的答案內容，值和thought保持一致
    answer_token_count = Column(
        Integer,
        nullable=False,
        server_default=text("0")
    )  # LLM生成答案消耗token數
    answer_unit_price = Column(
        Numeric(10, 7),
        nullable=False,
        server_default=text("0.0")
    )  # 單價，所有LLM的計算方式統一為CNY
    answer_price_unit = Column(
        Numeric(10, 4),
        nullable=False,
        server_default=text("0.0"),
    )  # 價格單位，值為1000代表1000token對應的單價

    # Agent推理觀察統計相關
    total_token_count = Column(
        Integer,
        nullable=False,
        server_default=text("0")
    )  # 總消耗token
    total_price = Column(
        Numeric(10, 7),
        nullable=False,
        server_default=text("0.0")
    )  # 總消耗
    latency = Column(
        Float,
        nullable=False,
        server_default=text("0.0")
    )  # 推理觀察步驟耗時

    # 時間相關資訊
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )  # 更新時間
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)')
    )  # 創建時間
