#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/4 下午6:59
@Author : zsting29@gmail.com
@File   : account.py
"""
from datetime import datetime

from flask import current_app
from sqlalchemy import PrimaryKeyConstraint, Column, String, text, DateTime, UUID

from internal.entity.conversation_entity import InvokeFrom
from internal.extension.database_extension import db
from .conversation import Conversation


class Account(db.Model):
    __tablename__ = "account"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_account_id"),
        # Index("account_email_idx", "email"),
    )

    id = Column(
        UUID, nullable=False,
        server_default=text("uuid_generate_v4()"))
    name = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    email = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    avatar = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    password = Column(
        String(255),
        nullable=True,
        server_default=text("''::character varying")
    )
    password_salt = Column(
        String(255),
        nullable=True,
        server_default=text("''::character varying")
    )
    assistant_agent_conversation_id = Column(
        UUID,
        nullable=True
    )  # 辅助智能体会话id
    last_login_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)")
    )
    last_login_ip = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)")
    )

    @property
    def is_password_set(self) -> bool:
        """只讀屬性，獲取當前帳號的密碼是否設置"""
        return self.password is not None and self.password != ""

    @property
    def assistant_agent_conversation(self) -> "Conversation":
        """只讀屬性，返回當前帳號的輔助Agent會話"""
        # 1.獲取輔助Agent應用id
        assistant_agent_id = current_app.config.get("ASSISTANT_AGENT_ID")
        conversation = db.session.query(Conversation).get(
            self.assistant_agent_conversation_id
        ) if self.assistant_agent_conversation_id else None

        # 2.判斷會話資訊是否存在，如果不存在則創建一個空會話
        if not self.assistant_agent_conversation_id or not conversation:
            # 3.開啟自動提交上下文
            with db.auto_commit():
                # 4.創建輔助Agent會話
                conversation = Conversation(
                    app_id=assistant_agent_id,
                    name="New Conversation",
                    invoke_from=InvokeFrom.ASSISTANT_AGENT,
                    created_by=self.id,
                )
                db.session.add(conversation)
                db.session.flush()

                # 5.更新當前帳號的輔助Agent會話id
                self.assistant_agent_conversation_id = conversation.id

        return conversation


class AccountOAuth(db.Model):
    """帳號與第三方授權認證記錄表"""
    __tablename__ = "account_oauth"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_account_oauth_id"),
        # Index("account_oauth_account_id_idx", "account_id"),
        # Index("account_oauth_openid_provider_idx", "openid", "provider"),
    )

    id = Column(
        UUID,
        nullable=False,
        server_default=text("uuid_generate_v4()")
    )
    account_id = Column(
        UUID,
        nullable=False
    )
    provider = Column(
        String(255), nullable=False,
        server_default=text("''::character varying")
    )
    openid = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    encrypted_token = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)")
    )
