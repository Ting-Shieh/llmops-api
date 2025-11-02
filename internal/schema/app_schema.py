#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/28 下午5:25
@Author : zsting29@gmail.com
@File   : app_schema.py
"""
from urllib.parse import urlparse
from uuid import UUID

from flask_wtf import FlaskForm
from marshmallow import fields, pre_dump, Schema
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError, URL

from internal.entity.app_entity import AppStatus
from internal.lib.helper import datetime_to_timestamp
from internal.model import Message, App, AppConfigVersion
from internal.schema import ListField
from pkg.paginator import PaginatorReq


class CreateAppReq(FlaskForm):
    """創建Agent應用請求結構體"""
    name = StringField("name", validators=[
        DataRequired("應用名稱不能為空"),
        Length(max=40, message="應用名稱長度最大不能超過40個字元"),
    ])
    icon = StringField("icon", validators=[
        DataRequired("應用圖示不能為空"),
        URL(message="應用圖示必須是圖片URL連結"),
    ])
    description = StringField("description", validators=[
        Length(max=800, message="應用描述的長度不能超過800個字元")
    ])


class UpdateAppReq(FlaskForm):
    """更新Agent應用請求結構體"""
    name = StringField("name", validators=[
        DataRequired("應用名稱不能為空"),
        Length(max=40, message="應用名稱長度最大不能超過40個字元"),
    ])
    icon = StringField("icon", validators=[
        DataRequired("應用圖示不能為空"),
        URL(message="應用圖示必須是圖片URL連結"),
    ])
    description = StringField("description", validators=[
        Length(max=800, message="應用描述的長度不能超過800個字元")
    ])


class GetAppsWithPageReq(PaginatorReq):
    """獲取應用分頁列表數據請求"""
    search_word = StringField("search_word", default="", validators=[Optional()])


class GetAppResp(Schema):
    """獲取應用基礎資訊響應結構"""
    id = fields.UUID(dump_default="")
    debug_conversation_id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    status = fields.String(dump_default="")
    draft_updated_at = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: App, **kwargs):
        return {
            "id": data.id,
            "debug_conversation_id": data.debug_conversation_id if data.debug_conversation_id else "",
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "status": data.status,
            "draft_updated_at": datetime_to_timestamp(data.draft_app_config.updated_at),
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class GetAppsWithPageResp(Schema):
    """獲取應用分頁列表數據響應結構"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    preset_prompt = fields.String(dump_default="")
    model_config = fields.Dict(dump_default={})
    status = fields.String(dump_default="")
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: App, **kwargs):
        app_config = data.app_config if data.status == AppStatus.PUBLISHED else data.draft_app_config
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "preset_prompt": app_config.preset_prompt,
            "model_config": {
                "provider": app_config.model_config.get("provider", ""),
                "model": app_config.model_config.get("model", "")
            },
            "status": data.status,
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class GetPublishHistoriesWithPageReq(PaginatorReq):
    """獲取應用發布歷史配置分頁列表請求"""
    ...


class GetPublishHistoriesWithPageResp(Schema):
    """獲取應用發布歷史配置列表分頁數據"""
    id = fields.UUID(dump_default="")
    version = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: AppConfigVersion, **kwargs):
        return {
            "id": data.id,
            "version": data.version,
            "created_at": datetime_to_timestamp(data.created_at),
        }


class FallbackHistoryToDraftReq(FlaskForm):
    """回退歷史版本到草稿請求結構體"""
    app_config_version_id = StringField("app_config_version_id", validators=[
        DataRequired("回退配置版本id不能為空")
    ])

    def validate_app_config_version_id(self, field: StringField) -> None:
        """校驗回退配置版本id"""
        try:
            UUID(field.data)
        except Exception as e:
            raise ValidationError("回退配置版本id必須為UUID")


class UpdateDebugConversationSummaryReq(FlaskForm):
    """更新應用除錯會話長期記憶請求體"""
    summary = StringField("summary", default="")


class DebugChatReq(FlaskForm):
    """應用除錯會話請求結構體"""
    image_urls = ListField("image_urls", default=[])
    query = StringField("query", validators=[
        DataRequired("用戶提問query不能為空"),
    ])

    def validate_image_urls(self, field: ListField) -> None:
        """校驗傳遞的圖片URL連結列表"""
        # 1.校驗數據類型如果為None則設置預設值空列表
        if not isinstance(field.data, list):
            return []

        # 2.校驗數據的長度，最多不能超過5條URL記錄
        if len(field.data) > 5:
            raise ValidationError("上傳的圖片數量不能超過5，請核實後重試")

        # 3.循環校驗image_url是否為URL
        for image_url in field.data:
            result = urlparse(image_url)
            if not all([result.scheme, result.netloc]):
                raise ValidationError("上傳的圖片URL地址格式錯誤，請核實後重試")


class GetDebugConversationMessagesWithPageReq(PaginatorReq):
    """獲取除錯會話消息列表分頁請求結構體"""
    created_at = IntegerField("created_at", default=0, validators=[
        Optional(),
        NumberRange(min=0, message="created_at游標最小值為0")
    ])


class GetDebugConversationMessagesWithPageResp(Schema):
    """獲取除錯會話消息列表分頁響應結構體"""
    id = fields.UUID(dump_default="")
    conversation_id = fields.UUID(dump_default="")
    query = fields.String(dump_default="")
    image_urls = fields.List(fields.String, dump_default=[])
    answer = fields.String(dump_default="")
    total_token_count = fields.Integer(dump_default=0)
    latency = fields.Float(dump_default=0)
    agent_thoughts = fields.List(fields.Dict, dump_default=[])
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Message, **kwargs):
        return {
            "id": data.id,
            "conversation_id": data.conversation_id,
            "query": data.query,
            "image_urls": data.image_urls,
            "answer": data.answer,
            "total_token_count": data.total_token_count,
            "latency": data.latency,
            "agent_thoughts": [{
                "id": agent_thought.id,
                "position": agent_thought.position,
                "event": agent_thought.event,
                "thought": agent_thought.thought,
                "observation": agent_thought.observation,
                "tool": agent_thought.tool,
                "tool_input": agent_thought.tool_input,
                "latency": agent_thought.latency,
                "created_at": datetime_to_timestamp(agent_thought.created_at),
            } for agent_thought in data.agent_thoughts],
            "created_at": datetime_to_timestamp(data.created_at),
        }
