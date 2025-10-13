#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/13 下午11:38
@Author : zsting29@gmail.com
@File   : oauth_handler.py
"""
from dataclasses import dataclass

from injector import inject

from internal.schema.oauth_schema import AuthorizeReq, AuthorizeResp
from internal.service import OAuthService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class OAuthHandler:
    """第三方授權認證處理器"""
    oauth_service: OAuthService

    def provider(self, provider_name: str):
        """根據傳遞的提供商名字獲取授權認證重定向地址"""
        # 1.根據provider_name獲取授權服務提供商
        oauth = self.oauth_service.get_oauth_by_provider_name(provider_name)

        # 2.調用函數獲取授權地址
        redirect_url = oauth.get_authorization_url()

        return success_json({"redirect_url": redirect_url})

    def authorize(self, provider_name: str):
        """根據傳遞的提供商名字+code獲取第三方授權資訊"""
        # 1.提取請求數據並校驗
        req = AuthorizeReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務登入帳號
        credential = self.oauth_service.oauth_login(provider_name, req.code.data)

        return success_json(AuthorizeResp().dump(credential))
