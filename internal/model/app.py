#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/14 下午9:49
@Author : zsting29@gmail.com
@File   : main.py
"""
from datetime import datetime

from sqlalchemy import Column, UUID, String, DateTime, Text, PrimaryKeyConstraint, Index, text

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


class AppDatasetJoin(db.Model):
    """應用知識庫關聯表"""
    __tablename__ = "app_dataset_join"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_dataset_join_id"),
        # Index("app_dataset_join_app_id_dataset_id_idx", "app_id", "dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    app_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
