#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/28 下午1:44
@Author : zsting29@gmail.com
@File   : workflow_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Regexp, URL, Optional, AnyOf

from internal.core.workflow.entities.workflow_entity import WORKFLOW_CONFIG_NAME_PATTERN
from internal.entity.workflow_entity import WorkflowStatus
from internal.lib.helper import datetime_to_timestamp
from internal.model import Workflow
from pkg.paginator import PaginatorReq


class CreateWorkflowReq(FlaskForm):
    """創建工作流基礎請求"""
    name = StringField("name", validators=[
        DataRequired("工作流名稱不能為空"),
        Length(max=50, message="工作流名稱長度不能超過50"),
    ])
    tool_call_name = StringField("tool_call_name", validators=[
        DataRequired("英文名稱不能為空"),
        Length(max=50, message="英文名稱不能超過50個字元"),
        Regexp(WORKFLOW_CONFIG_NAME_PATTERN, message="英文名稱僅支持字母、數字和下劃線，且以字母/下劃線為開頭")
    ])
    icon = StringField("icon", validators=[
        DataRequired("工作流圖示不能為空"),
        URL(message="工作流圖示必須是圖片URL地址"),
    ])
    description = StringField("description", validators=[
        DataRequired("工作流描述不能為空"),
        Length(max=1024, message="工作流描述不能超過1024個字元")
    ])


class UpdateWorkflowReq(FlaskForm):
    """創建工作流基礎請求"""
    name = StringField("name", validators=[
        DataRequired("工作流名稱不能為空"),
        Length(max=50, message="工作流名稱長度不能超過50"),
    ])
    tool_call_name = StringField("tool_call_name", validators=[
        DataRequired("英文名稱不能為空"),
        Length(max=50, message="英文名稱不能超過50個字元"),
        Regexp(WORKFLOW_CONFIG_NAME_PATTERN, message="英文名稱僅支持字母、數字和下劃線，且以字母/下劃線為開頭")
    ])
    icon = StringField("icon", validators=[
        DataRequired("工作流圖示不能為空"),
        URL(message="工作流圖示必須是圖片URL地址"),
    ])
    description = StringField("description", validators=[
        DataRequired("工作流描述不能為空"),
        Length(max=1024, message="工作流描述不能超過1024個字元")
    ])


class GetWorkflowResp(Schema):
    """獲取工作流詳情響應結構"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    tool_call_name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    status = fields.String(dump_default="")
    is_debug_passed = fields.Boolean(dump_default=False)
    node_count = fields.Integer(dump_default=0)
    published_at = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Workflow, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "tool_call_name": data.tool_call_name,
            "icon": data.icon,
            "description": data.description,
            "status": data.status,
            "is_debug_passed": data.is_debug_passed,
            "node_count": len(data.draft_graph.get("nodes", [])),
            "published_at": datetime_to_timestamp(data.published_at),
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class GetWorkflowsWithPageReq(PaginatorReq):
    """獲取工作流分頁列表數據請求結構"""
    status = StringField("status", default="", validators=[
        Optional(),
        AnyOf(WorkflowStatus.__members__.values(), message="工作流狀態格式錯誤")
    ])
    search_word = StringField("search_word", default="", validators=[Optional()])


class GetWorkflowsWithPageResp(Schema):
    """獲取工作流分頁列表數據響應結構"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    tool_call_name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    status = fields.String(dump_default="")
    is_debug_passed = fields.Boolean(dump_default=False)
    node_count = fields.Integer(dump_default=0)
    published_at = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Workflow, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "tool_call_name": data.tool_call_name,
            "icon": data.icon,
            "description": data.description,
            "status": data.status,
            "is_debug_passed": data.is_debug_passed,
            "node_count": len(data.graph.get("nodes", [])),
            "published_at": datetime_to_timestamp(data.published_at),
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }
