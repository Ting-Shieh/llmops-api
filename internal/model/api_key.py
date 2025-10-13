#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/12 下午1:41
@Author : zsting29@gmail.com
@File   : api_key.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    String,
    DateTime,
    Boolean,
    text,
    PrimaryKeyConstraint,
)

from internal.extension.database_extension import db
from internal.model import Account


class ApiKey(db.Model):
    """API秘鑰模型"""
    __tablename__ = "api_key"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_key_id"),
        # Index("api_key_account_id_idx", "account_id"),
        # Index("api_key_api_key_idx", "api_key"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 記錄id
    account_id = Column(UUID, nullable=False)  # 關聯帳號id
    api_key = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 加密後的api秘鑰
    is_active = Column(Boolean, nullable=False, server_default=text('false'))  # 是否啟用，為true時可以使用
    remark = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 備註資訊
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))

    @property
    def account(self) -> "Account":
        """只讀屬性，返回該秘鑰歸屬的帳號資訊"""
        return db.session.query(Account).get(self.account_id)
