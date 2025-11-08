#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/2 下午6:49
@Author : zsting29@gmail.com
@File   : ai_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.ai_schema import OptimizePromptReq, GenerateSuggestedQuestionsReq
from internal.service import AIService
from pkg.response import validate_error_json, compact_generate_response, success_json


@inject
@dataclass
class AIHandler:
    """AI輔助模組處理器"""
    ai_service: AIService

    @login_required
    def optimize_prompt(self):
        """根據傳遞的預設prompt進行最佳化"""
        # 1.提取請求並校驗
        req = OptimizePromptReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務最佳化prompt
        resp = self.ai_service.optimize_prompt(req.prompt.data)

        return compact_generate_response(resp)

    @login_required
    def generate_suggested_questions(self):
        """根據傳遞的消息id生成建議問題列表"""
        # 1.提取請求並校驗
        req = GenerateSuggestedQuestionsReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務生成建議問題列表
        suggested_questions = self.ai_service.generate_suggested_questions_from_message_id(
            req.message_id.data,
            current_user,
        )

        return success_json(suggested_questions)
