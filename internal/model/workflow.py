#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/8 下午7:15
@Author : zsting29@gmail.com
@File   : workflow.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    text,
    PrimaryKeyConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class Workflow(db.Model):
    """工作流模型"""
    __tablename__ = "workflow"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_workflow_id"),
        Index("workflow_account_id_idx", "account_id"),
        Index("workflow_tool_call_name_idx", "tool_call_name"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)  # 創建帳號id
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 工作流名字
    tool_call_name = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 工作流工具調用名字
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 工作流圖示
    description = Column(Text, nullable=False, server_default=text("''::text"))  # 應用描述
    graph = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 運行時配置
    draft_graph = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 草稿圖配置
    is_debug_passed = Column(Boolean, nullable=False, server_default=text("false"))  # 是否除錯通過
    status = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 工作流狀態
    published_at = Column(DateTime, nullable=True)  # 發布時間
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


class WorkflowResult(db.Model):
    """工作流儲存結果模型"""
    __tablename__ = "workflow_result"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_workflow_result_id"),
        Index("workflow_result_app_id_idx", "app_id"),
        Index("workflow_result_account_id_idx", "account_id"),
        Index("workflow_result_workflow_id_idx", "workflow_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 結果id
    app_id = Column(UUID, nullable=True)  # 工作流調用的應用id，如果為空則代表非應用調用
    account_id = Column(UUID, nullable=False)  # 創建帳號id
    workflow_id = Column(UUID, nullable=False)  # 結果關聯的工作流id
    graph = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 運行時配置
    state = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 工作流最終狀態
    latency = Column(Float, nullable=False, server_default=text("0.0"))  # 消息的總耗時
    status = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 運行狀態
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
