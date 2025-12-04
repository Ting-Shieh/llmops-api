#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/26 下午11:38
@Author : zsting29@gmail.com
@File   : openapi_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.openapi_schema import OpenAPIChatReq
from internal.service import OpenAPIService
from pkg.response import validate_error_json, compact_generate_response


@inject
@dataclass
class OpenAPIHandler:
    """開放API處理器"""
    openapi_service: OpenAPIService

    @login_required
    def chat(self):
        """開放Chat對話介面"""
        # 1.提取請求並校驗數據
        req = OpenAPIChatReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建會話
        resp = self.openapi_service.chat(req, current_user)

        return compact_generate_response(resp)
