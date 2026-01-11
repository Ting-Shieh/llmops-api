#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/28 下午1:15
@Author : zsting29@gmail.com
@File   : workflow_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import current_user, login_required
from injector import inject

from internal.schema.workflow_schema import (
    CreateWorkflowReq,
    UpdateWorkflowReq,
    GetWorkflowResp,
    GetWorkflowsWithPageReq,
    GetWorkflowsWithPageResp,
)
from internal.service import WorkflowService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message, compact_generate_response


@inject
@dataclass
class WorkflowHandler:
    """工作流處理器"""
    workflow_service: WorkflowService

    @login_required
    def create_workflow(self):
        """新增工作流"""
        # 1.提取請求並校驗
        req = CreateWorkflowReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建工作流
        workflow = self.workflow_service.create_workflow(req, current_user)

        return success_json({"id": workflow.id})

    @login_required
    def delete_workflow(self, workflow_id: UUID):
        """根據傳遞的工作流id刪除指定的工作流"""
        self.workflow_service.delete_workflow(workflow_id, current_user)
        return success_message("刪除工作流成功")

    @login_required
    def update_workflow(self, workflow_id: UUID):
        """根據傳遞的工作流id獲取工作流詳情"""
        # 1.提取請求並校驗
        req = UpdateWorkflowReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新工作流數據
        self.workflow_service.update_workflow(workflow_id, current_user, **req.data)

        return success_message("修改工作流基礎資訊成功")

    @login_required
    def get_workflow(self, workflow_id: UUID):
        """根據傳遞的工作流id獲取工作流詳情"""
        workflow = self.workflow_service.get_workflow(workflow_id, current_user)
        resp = GetWorkflowResp()
        return success_json(resp.dump(workflow))

    @login_required
    def get_workflows_with_page(self):
        """獲取當前登入帳號下的工作流分頁列表數據"""
        # 1.提取請求並校驗
        req = GetWorkflowsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.獲取分頁列表數據
        workflows, paginator = self.workflow_service.get_workflows_with_page(req, current_user)

        # 3.構建響應並返回
        resp = GetWorkflowsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(workflows), paginator=paginator))

    @login_required
    def update_draft_graph(self, workflow_id: UUID):
        """根據傳遞的工作流id+請求資訊更新工作流草稿圖配置"""
        # 1.提取草稿圖介面請求json數據
        draft_graph_dict = request.get_json(force=True, silent=True) or {
            "nodes": [],
            "edges": [],
        }

        # 2.調用服務更新工作流的草稿圖配置
        self.workflow_service.update_draft_graph(workflow_id, draft_graph_dict, current_user)

        return success_message("更新工作流草稿配置成功")

    @login_required
    def get_draft_graph(self, workflow_id: UUID):
        """根據傳遞的工作流id獲取該工作流的草稿配置資訊"""
        draft_graph = self.workflow_service.get_draft_graph(workflow_id, current_user)
        return success_json(draft_graph)

    @login_required
    def debug_workflow(self, workflow_id: UUID):
        """根據傳遞的變數字典+工作流id除錯指定的工作流"""
        # 1.提取用戶傳遞的輸入變數資訊
        inputs = request.get_json(force=True, silent=True) or {}

        # 2.調用服務除錯指定的API介面
        response = self.workflow_service.debug_workflow(workflow_id, inputs, current_user)

        return compact_generate_response(response)

    @login_required
    def publish_workflow(self, workflow_id: UUID):
        """根據傳遞的工作流id發布指定的工作流"""
        self.workflow_service.publish_workflow(workflow_id, current_user)
        return success_message("發布工作流成功")

    @login_required
    def cancel_publish_workflow(self, workflow_id: UUID):
        """根據傳遞的工作流id取消發布指定的工作流"""
        self.workflow_service.cancel_publish_workflow(workflow_id, current_user)
        return success_message("取消發布工作流成功")
