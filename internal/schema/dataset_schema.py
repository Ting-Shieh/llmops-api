#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/17 下午10:34
@Author : zsting29@gmail.com
@File   : dataset_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import (
    Schema,
    fields,
    pre_dump
)
from wtforms import (
    StringField,
    IntegerField,
    FloatField
)
from wtforms.validators import (
    DataRequired,
    Length,
    URL,
    Optional,
    AnyOf,
    NumberRange
)

from internal.entity.dataset_entity import RetrievalStrategy
from internal.lib.helper import datetime_to_timestamp
from internal.model import Dataset, DatasetQuery
from pkg.paginator import PaginatorReq


class CreateDatasetReq(FlaskForm):
    """創建知識庫請求"""
    name = StringField(
        "name",
        validators=[
            DataRequired(message="知識庫名稱不能為空"),
            Length(max=100, message="知識庫名稱長度不能超過100字符")
        ]
    )

    icon = StringField("icon", validators=[
        DataRequired("知識庫圖標不能為空"),
        URL("知識庫圖標必須是圖片URL地址"),
    ])
    description = StringField("description", default="", validators=[
        Optional(),
        Length(max=2000, message="知識庫描述長度不能超過2000字符")
    ])


class GetDatasetResp(Schema):
    """獲取知識庫詳情響應結構"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        # 動態刷新 GCS 簽名 URL
        icon_url = self._refresh_gcs_url(data.icon)
        
        return {
            "id": data.id,
            "name": data.name,
            "icon": icon_url,
            "description": data.description,
            "document_count": data.document_count,
            "hit_count": data.hit_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }
    
    @staticmethod
    def _refresh_gcs_url(url: str) -> str:
        """刷新 GCS 簽名 URL，如果是過期的 GCS URL 則重新生成"""
        if not url or "storage.googleapis.com" not in url:
            return url
        
        try:
            import re
            from internal.service.gcs_service import GcsService
            
            # 從 URL 中提取 key（檔案路徑）
            match = re.search(r'llmops_dev/(.+?)(?:\?|$)', url)
            if match:
                key = match.group(1)
                # 重新生成 7 天有效期的 URL
                return GcsService.get_file_url(key, signed=True, expiration_minutes=60 * 24 * 7)
        except Exception:
            # 如果解析失敗，返回原 URL
            pass
        
        return url


class UpdateDatasetReq(FlaskForm):
    """更新知識庫请求"""
    name = StringField("name", validators=[
        DataRequired("知識庫名稱不能為空"),
        Length(max=100, message="知識庫名稱長度不能超過100字符"),
    ])
    icon = StringField("icon", validators=[
        DataRequired("知識庫圖標不能为空"),
        URL("知識庫圖標必須是圖片URL地址"),
    ])
    description = StringField("description", default="", validators=[
        Optional(),
        Length(max=2000, message="知識庫描述長度不能超過2000字符")
    ])


class GetDatasetsWithPageReq(PaginatorReq):
    """獲取知識庫分頁列請求數據"""
    search_word = StringField("search_word", default="", validators=[
        Optional(),
    ])


class GetDatasetsWithPageResp(Schema):
    """獲取知識庫分頁列表響應數據"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        # 動態刷新 GCS 簽名 URL
        icon_url = self._refresh_gcs_url(data.icon)
        
        return {
            "id": data.id,
            "name": data.name,
            "icon": icon_url,
            "description": data.description,
            "document_count": data.document_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }
    
    @staticmethod
    def _refresh_gcs_url(url: str) -> str:
        """刷新 GCS 簽名 URL，如果是過期的 GCS URL 則重新生成"""
        if not url or "storage.googleapis.com" not in url:
            return url
        
        try:
            import re
            from internal.service.gcs_service import GcsService
            
            # 從 URL 中提取 key（檔案路徑）
            # 例如：https://storage.googleapis.com/llmops_dev/2025/06/19/uuid.png?Expires=...
            # 提取：2025/06/19/uuid.png
            match = re.search(r'llmops_dev/(.+?)(?:\?|$)', url)
            if match:
                key = match.group(1)
                # 重新生成 7 天有效期的 URL
                return GcsService.get_file_url(key, signed=True, expiration_minutes=60 * 24 * 7)
        except Exception:
            # 如果解析失敗，返回原 URL
            pass
        
        return url


class HitReq(FlaskForm):
    """知識庫召回測試請求"""
    query = StringField("query", validators=[
        DataRequired("查詢語句不能為空"),
        Length(max=200, message="查詢語句的最大長度不能超過200")
    ])
    retrieval_strategy = StringField("retrieval_strategy", validators=[
        DataRequired("檢索策略不能為空"),
        AnyOf(
            [item.value for item in RetrievalStrategy],
            message="檢索策略格式錯誤"
        )
    ])
    k = IntegerField("k", validators=[
        DataRequired("最大召回數量不能為空"),
        NumberRange(min=1, max=10, message="最大召回數量的範圍在1-10")
    ])
    score = FloatField("score", validators=[
        NumberRange(min=0, max=0.99, message="最小匹配度範圍在0-0.99")
    ])


class GetDatasetQueriesResp(Schema):
    """獲取知識庫最近查詢響應結構"""
    id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    query = fields.String(dump_default="")
    source = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: DatasetQuery, **kwargs):
        return {
            "id": data.id,
            "dataset_id": data.dataset_id,
            "query": data.query,
            "source": data.source,
            "created_at": datetime_to_timestamp(data.created_at),
        }
