#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/14 下午9:49
@Author : zsting29@gmail.com
@File   : main.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    String,
    DateTime,
    Text,
    PrimaryKeyConstraint,
    Index,
    text, Integer
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class App(db.Model):
    """AI應用模型"""
    __tablename__ = "app"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        Index("idx_app_account_id", "account_id")
    )

    id = Column(
        UUID,
        nullable=False,
        server_default=text("uuid_generate_v4()")
    )
    account_id = Column(UUID)
    name = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    icon = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    description = Column(
        Text, nullable=False,
        server_default=text("''::text")
    )
    status = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    # config = Column(JSONB, default={}, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)")
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)")
    )


class AppConfig(db.Model):
    """應用配置模型"""
    __tablename__ = "app_config"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_id"),
        # Index("app_config_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 配置id
    app_id = Column(UUID, nullable=False)  # 關聯應用id
    model_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 模型配置
    dialog_round = Column(Integer, nullable=False, server_default=text("0"))  # 鞋帶上下文輪數
    preset_prompt = Column(Text, nullable=False, server_default=text("''::text"))  # 預設prompt
    tools = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 應用關聯工具列表
    workflows = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 應用關聯的工作流列表
    retrieval_config = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 檢索配置
    long_term_memory = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 長期記憶配置
    opening_statement = Column(Text, nullable=False, server_default=text("''::text"))  # 開場白文案
    opening_questions = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 開場白建議問題列表
    speech_to_text = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 語音轉文本配置
    text_to_speech = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 文本轉語音配置
    suggested_after_answer = Column(
        JSONB,
        nullable=False,
        server_default=text("'{\"enable\": true}'::jsonb"),
    )  # 回答後生成建議問題
    review_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 審核配置
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))

    @property
    def app_dataset_joins(self) -> list["AppDatasetJoin"]:
        """只讀屬性，獲取配置的知識庫關聯記錄"""
        return (
            db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == self.app_id
            ).all()
        )


class AppConfigVersion(db.Model):
    """應用配置版本歷史表，用於儲存草稿配置+歷史發布配置"""
    __tablename__ = "app_config_version"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_version_id"),
        # Index("app_config_version_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 配置id
    app_id = Column(UUID, nullable=False)  # 關聯應用id
    model_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 模型配置
    dialog_round = Column(Integer, nullable=False, server_default=text("0"))  # 鞋帶上下文輪數
    preset_prompt = Column(Text, nullable=False, server_default=text("''::text"))  # 人設與回復邏輯
    tools = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 應用關聯的工具列表
    workflows = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 應用關聯的工作流列表
    datasets = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 應用關聯的知識庫列表
    retrieval_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 檢索配置
    long_term_memory = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 長期記憶配置
    opening_statement = Column(Text, nullable=False, server_default=text("''::text"))  # 開場白文案
    opening_questions = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 開場白建議問題列表
    speech_to_text = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 語音轉文本配置
    text_to_speech = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 文本轉語音配置
    suggested_after_answer = Column(
        JSONB,
        nullable=False,
        server_default=text("'{\"enable\": true}'::jsonb"),
    )  # 回答後生成建議問題
    review_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 審核配置
    version = Column(Integer, nullable=False, server_default=text("0"))  # 發布版本號
    config_type = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 配置類型
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class AppDatasetJoin(db.Model):
    """應用知識庫關聯表"""
    __tablename__ = "app_dataset_join"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_dataset_join_id"),
        # Index("app_dataset_join_app_id_dataset_id_idx", "app_id", "dataset_id"),
    )

    id = Column(
        UUID,
        nullable=False,
        server_default=text("uuid_generate_v4()")
    )
    app_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
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
