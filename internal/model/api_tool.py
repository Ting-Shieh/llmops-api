#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/11 下午11:08
@Author : zsting29@gmail.com
@File   : api_tool.py
"""
from sqlalchemy import Column, UUID, text, DateTime, Text, String, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class ApiToolProvider(db.Model):
    """API工具提供商模型"""
    __tablename__ = "api_tool_provider"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_provider_id"),
        # UniqueConstraint("account_id", "name", name="uk_api_tool_provider_account_id_name"),
        # Index("idx_api_tool_provider_account_id", "account_id")
    )

    id = Column(UUID, nullable=False, server_default=text('uuid_generate_v4()'))
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    openai_schema = Column(Text, nullable=False, server_default=text("''::text"))
    headers = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)')
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class ApiTool(db.Model):
    """API工具表"""
    __tablename__ = "api_tool"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_id"),
        # UniqueConstraint("account_id", "provider_id", "name", name="uk_api_tool_account_id_provider_id_name"),
    )

    id = Column(UUID, nullable=False, server_default=text('uuid_generate_v4()'))
    account_id = Column(UUID, nullable=False)
    provider_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    url = Column(String(255), nullable=False, server_default=text("''::character varying"))
    method = Column(String(255), nullable=False, server_default=text("''::character varying"))
    parameters = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)')
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


@property
def provider(self) -> "ApiToolProvider":
    """只讀屬性，返回當前工具關聯/歸屬的工具提供者訊息"""
    return db.session.query(ApiToolProvider).get(self.provider_id)
