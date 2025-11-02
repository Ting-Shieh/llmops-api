#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/14 下午9:49
@Author : zsting29@gmail.com
@File   : main.py
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    UUID,
    String,
    DateTime,
    Text,
    PrimaryKeyConstraint,
    text, Integer, func
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.entity.app_entity import AppConfigType, DEFAULT_APP_CONFIG, AppStatus
from internal.entity.conversation_entity import InvokeFrom
from internal.extension.database_extension import db
from internal.lib.helper import generate_random_string
from .conversation import Conversation


class App(db.Model):
    """AI應用模型"""
    __tablename__ = "app"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        # Index("idx_app_account_id", "account_id")
    )

    id = Column(
        UUID,
        nullable=False,
        default=uuid4,
        server_default=text("uuid_generate_v4()")
    )
    account_id = Column(UUID, nullable=False)
    name = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    app_config_id = Column(
        UUID,
        nullable=True
    )  # 發布配置id，當值為空時代表沒有發布
    draft_app_config_id = Column(
        UUID,
        nullable=True
    )  # 關聯的草稿配置id
    debug_conversation_id = Column(
        UUID,
        nullable=True
    )  # 應用除錯會話id，為None則代表沒有會話資訊
    icon = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    description = Column(
        Text, nullable=False,
        server_default=text("''::text")
    )
    token = Column(
        String(255),
        nullable=True,
        server_default=text("''::character varying")
    )  # 應用憑證資訊
    status = Column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    # config = Column(JSONB, default={}, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=func.now()
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP(0)")
    )

    @property
    def app_config(self) -> "AppConfig":
        """只讀屬性，返回當前應用的運行配置"""
        if not self.app_config_id:
            return None
        return db.session.query(AppConfig).get(self.app_config_id)

    @property
    def draft_app_config(self) -> "AppConfigVersion":
        """只讀屬性，返回當前應用的草稿配置"""
        # 1.獲取當前應用的草稿配置
        app_config_version = db.session.query(AppConfigVersion).filter(
            AppConfigVersion.app_id == self.id,
            AppConfigVersion.config_type == AppConfigType.DRAFT,
        ).one_or_none()

        # 2.檢測配置是否存在，如果不存在則創建一個預設值
        if not app_config_version:
            app_config_version = AppConfigVersion(
                app_id=self.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG
            )
            db.session.add(app_config_version)
            db.session.commit()

        return app_config_version

    @property
    def debug_conversation(self) -> "Conversation":
        """獲取應用的除錯會話記錄"""
        # 1.根據debug_conversation_id獲取除錯會話記錄
        debug_conversation = None
        if self.debug_conversation_id is not None:
            debug_conversation = db.session.query(Conversation).filter(
                Conversation.id == self.debug_conversation_id,
                Conversation.invoke_from == InvokeFrom.DEBUGGER,
            ).one_or_none()

        # 2.檢測數據是否存在，如果不存在則創建
        if not self.debug_conversation_id or not debug_conversation:
            # 3.開啟資料庫自動提交上下文
            with db.auto_commit():
                # 4.創建應用除錯會話記錄並刷新獲取會話id
                debug_conversation = Conversation(
                    app_id=self.id,
                    name="New Conversation",
                    invoke_from=InvokeFrom.DEBUGGER,
                    created_by=self.account_id,
                )
                db.session.add(debug_conversation)
                db.session.flush()

                # 5.更新當前記錄的debug_conversation_id
                self.debug_conversation_id = debug_conversation.id

        return debug_conversation

    @property
    def token_with_default(self) -> str:
        """獲取帶有預設值的token"""
        # 1.判斷狀態是否為已發布
        if self.status != AppStatus.PUBLISHED:
            # 2.非發布的情況下需要清空數據，並提交更新
            if self.token is not None or self.token != "":
                self.token = None
                db.session.commit()
            return ""

        # 3.已發布狀態需要判斷token是否存在，不存在則生成
        if self.token is None or self.token == "":
            self.token = generate_random_string(16)
            db.session.commit()

        return self.token


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
    dialog_round = Column(Integer, nullable=False, server_default=text("0"))  # 協帶上下文輪數
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
