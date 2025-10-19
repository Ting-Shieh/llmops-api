#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/14 下午11:17
@Author : zsting29@gmail.com
@File   : auth_handler.py
"""
from dataclasses import dataclass

from flask_login import logout_user, login_required
from injector import inject

from internal.schema.auth_schema import PasswordLoginReq, PasswordLoginResp
from internal.service import AccountService
from pkg.response import success_message, validate_error_json, success_json


@inject
@dataclass
class AuthHandler:
    """LLMOps平台自有授權認證處理器"""
    account_service: AccountService

    def password_login(self):
        """帳號密碼登入"""
        # 1.提取請求並校驗數據
        req = PasswordLoginReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務登入帳號
        credential = self.account_service.password_login(req.email.data, req.password.data)

        # 3.創建響應結構並返回
        resp = PasswordLoginResp()

        return success_json(resp.dump(credential))

    @login_required
    def logout(self):
        """退出登錄，用於提示前端清除授權憑證"""
        logout_user()
        return success_message("退出登陸成功")
