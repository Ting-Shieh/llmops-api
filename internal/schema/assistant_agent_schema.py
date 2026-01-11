#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/1/6 下午8:28
@Author : zsting29@gmail.com
@File   : assistant_agent_schema.py
"""
from urllib.parse import urlparse

from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField, IntegerField
from wtforms.validators import (
    DataRequired,
    Optional,
    NumberRange,
    ValidationError
)

from internal.lib.helper import datetime_to_timestamp
from internal.model import Message
from pkg.paginator import PaginatorReq
from .schema import ListField


class AssistantAgentChat(FlaskForm):
    """輔助Agent會話請求結構體"""
    image_urls = ListField("image_urls", default=[])
    query = StringField("query", validators=[
        DataRequired("用戶提問query不能為空")
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


class GetAssistantAgentMessagesWithPageReq(PaginatorReq):
    """獲取輔助智慧體消息列表分頁請求"""
    created_at = IntegerField("created_at", default=0, validators=[
        Optional(),
        NumberRange(min=0, message="created_at游標最小值為0")
    ])


class GetAssistantAgentMessagesWithPageResp(Schema):
    """獲取輔助智慧體消息列表分頁響應結構"""
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
