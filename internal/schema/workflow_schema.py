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
        # 動態生成 icon 的 signed URL
        icon_url = self._refresh_gcs_url(data.icon) if data.icon else ""
        
        return {
            "id": data.id,
            "name": data.name,
            "tool_call_name": data.tool_call_name,
            "icon": icon_url,
            "description": data.description,
            "status": data.status,
            "is_debug_passed": data.is_debug_passed,
            "node_count": len(data.draft_graph.get("nodes", [])),
            "published_at": datetime_to_timestamp(data.published_at),
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }
    
    @staticmethod
    def _refresh_gcs_url(url: str) -> str:
        """刷新 GCS 簽名 URL，如果是過期的 GCS URL 則重新生成，如果是 key 則生成新的 signed URL"""
        if not url:
            return url
        
        try:
            import re
            from internal.service.gcs_service import GcsService
            
            # 如果已經是完整的 GCS URL，從中提取 key
            if "storage.googleapis.com" in url:
                match = re.search(r'llmops_dev/(.+?)(?:\?|$)', url)
                if match:
                    key = match.group(1)
                else:
                    return url  # 無法提取 key，返回原 URL
            else:
                # 如果只是 key（檔案路徑），直接使用
                key = url
            
            # 重新生成 7 天有效期的 URL
            return GcsService.get_file_url(key, signed=True, expiration_minutes=60 * 24 * 7)
        except Exception:
            # 如果解析失敗，返回原 URL
            return url


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
        # 動態生成 icon 的 signed URL
        icon_url = self._refresh_gcs_url(data.icon) if data.icon else ""
        
        return {
            "id": data.id,
            "name": data.name,
            "tool_call_name": data.tool_call_name,
            "icon": icon_url,
            "description": data.description,
            "status": data.status,
            "is_debug_passed": data.is_debug_passed,
            "node_count": len(data.graph.get("nodes", [])),
            "published_at": datetime_to_timestamp(data.published_at),
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }
    
    @staticmethod
    def _refresh_gcs_url(url: str) -> str:
        """刷新 GCS 簽名 URL，如果是過期的 GCS URL 則重新生成，如果是 key 則生成新的 signed URL"""
        if not url:
            return url
        
        try:
            import re
            from internal.service.gcs_service import GcsService
            
            # 如果已經是完整的 GCS URL，從中提取 key
            if "storage.googleapis.com" in url:
                match = re.search(r'llmops_dev/(.+?)(?:\?|$)', url)
                if match:
                    key = match.group(1)
                else:
                    return url  # 無法提取 key，返回原 URL
            else:
                # 如果只是 key（檔案路徑），直接使用
                key = url
            
            # 重新生成 7 天有效期的 URL
            return GcsService.get_file_url(key, signed=True, expiration_minutes=60 * 24 * 7)
        except Exception:
            # 如果解析失敗，返回原 URL
            return url
