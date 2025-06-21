#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/16 上午12:16
@Author : zsting29@gmail.com
@File   : dataset.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    DateTime,
    text,
    PrimaryKeyConstraint,
    Integer, Boolean, func,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db
from internal.model import AppDatasetJoin


class Dataset(db.Model):
    """知識庫表"""
    __tablename__ = "dataset"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_dataset_id"),
        # Index("dataset_account_id_name_idx", "account_id", "name"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    icon = Column(Text, nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))

    @property
    def document_count(self) -> int:
        """只讀屬性，獲取知識庫下的文檔數"""
        return (
            db.session.
            query(func.count(Document.id)).
            filter(Document.dataset_id == self.id).
            scalar()
        )

    @property
    def hit_count(self) -> int:
        """只讀屬性，獲取知識庫的命中次数"""
        return (
            db.session.
            query(func.coalesce(func.sum(Segment.hit_count), 0)).
            filter(Segment.dataset_id == self.id).
            scalar()
        )

    @property
    def related_app_count(self) -> int:
        """只讀屬性，獲取知識庫關聯的應用數"""
        return (
            db.session.
            query(func.count(AppDatasetJoin.id)).
            filter(AppDatasetJoin.dataset_id == self.id).
            scalar()
        )

    @property
    def character_count(self) -> int:
        """只讀屬性，獲取知識庫下的字符總數"""
        return (
            db.session.
            query(func.coalesce(func.sum(Document.character_count), 0)).
            filter(Document.dataset_id == self.id).
            scalar()
        )


class Document(db.Model):
    """文檔表"""
    __tablename__ = "document"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_document_id"),
        # Index("document_account_id_idx", "account_id"),
        # Index("document_dataset_id_idx", "dataset_id"),
        # Index("document_batch_idx", "batch"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    upload_file_id = Column(UUID, nullable=False)
    process_rule_id = Column(UUID, nullable=False)
    batch = Column(String(255), nullable=False, server_default=text("''::character varying"))
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    position = Column(Integer, nullable=False, server_default=text("1"))
    character_count = Column(Integer, nullable=False, server_default=text("0"))
    token_count = Column(Integer, nullable=False, server_default=text("0"))
    processing_started_at = Column(DateTime, nullable=True)
    parsing_completed_at = Column(DateTime, nullable=True)
    splitting_completed_at = Column(DateTime, nullable=True)
    indexing_completed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=False, server_default=text("''::text"))
    enabled = Column(Boolean, nullable=False, server_default=text("false"))
    disabled_at = Column(DateTime, nullable=True)
    status = Column(String(255), nullable=False, server_default=text("'waiting'::character varying"))
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


class Segment(db.Model):
    """片段表模型"""
    __tablename__ = "segment"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_segment_id"),
        # Index("segment_account_id_idx", "account_id"),
        # Index("segment_dataset_id_idx", "dataset_id"),
        # Index("segment_document_id_idx", "document_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    document_id = Column(UUID, nullable=False)
    node_id = Column(UUID, nullable=False)
    position = Column(Integer, nullable=False, server_default=text("1"))
    content = Column(Text, nullable=False, server_default=text("''::text"))
    character_count = Column(Integer, nullable=False, server_default=text("0"))
    token_count = Column(Integer, nullable=False, server_default=text("0"))
    keywords = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    hash = Column(String(255), nullable=False, server_default=text("''::character varying"))
    hit_count = Column(Integer, nullable=False, server_default=text("0"))
    enabled = Column(Boolean, nullable=False, server_default=text("false"))
    disabled_at = Column(DateTime, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    indexing_completed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=False, server_default=text("''::text"))
    status = Column(String(255), nullable=False, server_default=text("'waiting'::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class KeywordTable(db.Model):
    """關鍵詞表"""
    __tablename__ = "keyword_table"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_keyword_table_id"),
        # Index("keyword_table_dataset_id_idx", "dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    dataset_id = Column(UUID, nullable=False)
    keyword_table = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class DatasetQuery(db.Model):
    """知識庫查詢表"""
    __tablename__ = "dataset_query"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_dataset_query_id"),
        # Index("dataset_query_dataset_id_idx", "dataset_id"),
        # Index("dataset_created_by_idx", "created_by"),
        # Index("dataset_source_app_id_idx", "source_app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    dataset_id = Column(UUID, nullable=False)
    query = Column(Text, nullable=False, server_default=text("''::text"))
    source = Column(String(255), nullable=False, server_default=text("'HitTesting'::character varying"))
    source_app_id = Column(UUID, nullable=True)
    created_by = Column(UUID, nullable=True)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class ProcessRule(db.Model):
    """文檔處理規則表"""
    __tablename__ = "process_rule"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_process_rule_id"),
        # Index("process_rule_account_id_idx", "account_id"),
        # Index("process_rule_dataset_id_idx", "dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    mode = Column(String(255), nullable=False, server_default=text("'automic'::character varying"))
    rule = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))
