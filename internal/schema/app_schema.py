#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/28 下午5:25
@Author : zsting29@gmail.com
@File   : app_schema.py
"""
from urllib.parse import urlparse

from flask_wtf import FlaskForm
from marshmallow import fields, pre_dump, Schema
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError, URL

from internal.entity.app_entity import AppStatus
from internal.lib.helper import datetime_to_timestamp
from internal.model import Message, App
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


class GetAppsWithPageReq(PaginatorReq):
    """獲取應用分頁列表數據請求"""
    search_word = StringField("search_word", default="", validators=[Optional()])


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


class CompletionReq(FlaskForm):
    """基礎聊天接口請求驗證"""
    # required, max length=2000
    query = StringField("query", validators=[
        DataRequired(message="用戶提問為必填"),
        Length(max=2000, message="用戶的提問最大長度為2000"),
    ])


class DebugChatReq(FlaskForm):
    """应用调试会话请求结构体"""
    image_urls = ListField("image_urls", default=[])
    query = StringField("query", validators=[
        DataRequired("用户提问query不能为空"),
    ])

    def validate_image_urls(self, field: ListField) -> None:
        """校验传递的图片URL链接列表"""
        # 1.校验数据类型如果为None则设置默认值空列表
        if not isinstance(field.data, list):
            return []

        # 2.校验数据的长度，最多不能超过5条URL记录
        if len(field.data) > 5:
            raise ValidationError("上传的图片数量不能超过5，请核实后重试")

        # 3.循环校验image_url是否为URL
        for image_url in field.data:
            result = urlparse(image_url)
            if not all([result.scheme, result.netloc]):
                raise ValidationError("上传的图片URL地址格式错误，请核实后重试")


class GetDebugConversationMessagesWithPageReq(PaginatorReq):
    """获取调试会话消息列表分页请求结构体"""
    created_at = IntegerField("created_at", default=0, validators=[
        Optional(),
        NumberRange(min=0, message="created_at游标最小值为0")
    ])


class GetDebugConversationMessagesWithPageResp(Schema):
    """获取调试会话消息列表分页响应结构体"""
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
