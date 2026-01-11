#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/1/6 下午8:26
@Author : zsting29@gmail.com
@File   : assistant_agent_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.assistant_agent_schema import (
    AssistantAgentChat,
    GetAssistantAgentMessagesWithPageReq,
    GetAssistantAgentMessagesWithPageResp,
)
from internal.service import AssistantAgentService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, compact_generate_response, success_json, success_message


@inject
@dataclass
class AssistantAgentHandler:
    """輔助智慧體處理器"""
    assistant_agent_service: AssistantAgentService

    @login_required
    def assistant_agent_chat(self):
        """與輔助智慧體進行對話聊天"""
        # 1.提取請求數據並校驗
        req = AssistantAgentChat()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建會話響應
        response = self.assistant_agent_service.chat(req, current_user)

        return compact_generate_response(response)

    @login_required
    def stop_assistant_agent_chat(self, task_id: UUID):
        """停止與輔助智慧體的對話聊天"""
        self.assistant_agent_service.stop_chat(task_id, current_user)
        return success_message("停止輔助Agent會話成功")

    @login_required
    def get_assistant_agent_messages_with_page(self):
        """獲取與輔助智慧體的消息分頁列表"""
        # 1.提取請求並校驗數據
        req = GetAssistantAgentMessagesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務獲取數據
        messages, paginator = self.assistant_agent_service.get_conversation_messages_with_page(
            req, current_user
        )

        # 3.創建響應數據結構
        resp = GetAssistantAgentMessagesWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(messages), paginator=paginator))

    @login_required
    def delete_assistant_agent_conversation(self):
        """清空/刪除與輔助智慧體的聊天會話記錄"""
        # 1.調用服務清空輔助Agent會話列表
        self.assistant_agent_service.delete_conversation(current_user)

        # 2.清空成功後返回消息響應
        return success_message("清空輔助Agent會話成功")
