#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/9 下午9:46
@Author : zsting29@gmail.com
@File   : upload_file.py
"""
from sqlalchemy import Column, text, UUID, String, Integer, DateTime, PrimaryKeyConstraint

from internal.extension.database_extension import db


class UploadFile(db.Model):
    """上傳文件類型"""
    __tablename__ = "upload_file"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_upload_file_id"),
    )

    id = Column(UUID, nullable=False, server_default=text('uuid_generate_v4()'))
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    key = Column(String(255), nullable=False, server_default=text("''::character varying"))
    size = Column(Integer, nullable=False, server_default=text('0'))
    extension = Column(String(255), nullable=False, server_default=text("''::character varying"))
    mime_type = Column(String(255), nullable=False, server_default=text("''::character varying"))
    hash = Column(String(255), nullable=False, server_default=text("''::character varying"))
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

    @property
    def url(self) -> str:
        """
        動態生成文件的訪問 URL
        有效期設為 7 天，與用戶登入期間一致
        """
        from internal.service.gcs_service import GcsService
        return GcsService.get_file_url(
            key=self.key,
            signed=True,
            expiration_minutes=60 * 24 * 7  # 7 天
        )
