#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/25 下午11:49
@Author : zsting29@gmail.com
@File   : end_user.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    DateTime,
    text,
    PrimaryKeyConstraint,
)

from internal.extension.database_extension import db


class EndUser(db.Model):
    """終端用戶表模型"""
    __tablename__ = "end_user"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_end_user_id"),
        # Index("end_user_tenant_id_idx", "tenant_id"),
        # Index("end_user_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 終端id
    tenant_id = Column(UUID, nullable=False)  # 歸屬的帳號/空間id
    app_id = Column(UUID, nullable=False)  # 歸屬應用的id，終端用戶只能在應用一下使用
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))
