#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/13 下午11:47
@Author : zsting29@gmail.com
@File   : account_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.account_schema import GetCurrentUserResp, UpdatePasswordReq, UpdateNameReq, UpdateAvatarReq
from internal.service import AccountService
from pkg.response import success_json, validate_error_json, success_message


@inject
@dataclass
class AccountHandler:
    """帳號設定處理器"""
    account_service: AccountService

    @login_required
    def get_current_user(self):
        """獲取當前登入帳號資訊"""
        resp = GetCurrentUserResp()
        return success_json(resp.dump(current_user))

    @login_required
    def update_password(self):
        """更新當前登入帳號密碼"""
        # 1.提取請求數據並校驗
        req = UpdatePasswordReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新帳號密碼
        self.account_service.update_password(req.password.data, current_user)

        return success_message("更新帳號密碼成功")

    @login_required
    def update_name(self):
        """更新當前登入帳號名稱"""
        # 1.提取請求數據並校驗
        req = UpdateNameReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新帳號名稱
        self.account_service.update_account(current_user, name=req.name.data)

        return success_message("更新帳號名稱成功")

    @login_required
    def update_avatar(self):
        """更新當前帳號頭像資訊"""
        # 1.提取請求數據並校驗
        req = UpdateAvatarReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新帳號名稱
        self.account_service.update_account(current_user, avatar=req.avatar.data)

        return success_message("更新帳號頭像成功")
