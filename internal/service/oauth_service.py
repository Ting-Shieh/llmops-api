#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/13 下午11:37
@Author : zsting29@gmail.com
@File   : oauth_service.py
"""
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from flask import request
from injector import inject

from internal.exception import NotFoundException
from internal.model import AccountOAuth
from pkg.oauth import OAuth, GithubOAuth
from pkg.sqlalchemy import SQLAlchemy
from .account_service import AccountService
from .base_service import BaseService
from .jwt_service import JwtService


@inject
@dataclass
class OAuthService(BaseService):
    """第三方授權你認證服務"""
    db: SQLAlchemy
    jwt_service: JwtService
    account_service: AccountService

    @classmethod
    def get_all_oauth(cls) -> dict[str, OAuth]:
        """獲取LLMOps集成的所有第三方授權認證方式"""
        # 1.實例化集成的第三方授權認證OAuth
        github = GithubOAuth(
            client_id=os.getenv("GITHUB_CLIENT_ID"),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
            redirect_uri=os.getenv("GITHUB_REDIRECT_URI"),
        )

        # 2.構建字典並返回
        return {
            "github": github,
        }

    @classmethod
    def get_oauth_by_provider_name(cls, provider_name: str) -> OAuth:
        """根據傳遞的服務提供商名字獲取授權服務"""
        all_oauth = cls.get_all_oauth()
        oauth = all_oauth.get(provider_name)

        if oauth is None:
            raise NotFoundException(f"該授權方式[{provider_name}]不存在")

        return oauth

    def oauth_login(self, provider_name: str, code: str) -> dict[str, Any]:
        """第三方OAuth授權認證登錄，返回授權憑證以及過期時間"""
        # 1.根據傳遞的provider_name獲取oauth
        oauth = self.get_oauth_by_provider_name(provider_name)

        # 2.根據code從第三方登錄服務中獲取access_token
        oauth_access_token = oauth.get_access_token(code)

        # 3.根據獲取到的token提取user_info資訊
        oauth_user_info = oauth.get_user_info(oauth_access_token)

        # 4.根據provider_name+openid獲取授權記錄
        account_oauth = self.account_service.get_account_oauth_by_provider_name_and_openid(
            provider_name,
            oauth_user_info.id,
        )
        if not account_oauth:
            # 5.該授權認證方式是第一次登錄，查詢信箱是否存在
            account = self.account_service.get_account_by_email(oauth_user_info.email)
            if not account:
                # 6.帳號不存在，註冊帳號
                account = self.account_service.create_account(
                    name=oauth_user_info.name,
                    email=oauth_user_info.email,
                )
            # 7.添加授權認證記錄
            account_oauth = self.create(
                AccountOAuth,
                account_id=account.id,
                provider=provider_name,
                openid=oauth_user_info.id,
                encrypted_token=oauth_access_token,
            )
        else:
            # 8.尋找帳號資訊
            account = self.account_service.get_account(account_oauth.account_id)

        # 9.更新帳號資訊，涵蓋最後一次登錄時間，以及ip地址
        self.update(
            account,
            last_login_at=datetime.now(),
            last_login_ip=request.remote_addr,
        )
        self.update(
            account_oauth,
            encrypted_token=oauth_access_token,
        )

        # 10.生成授權憑證資訊
        expire_at = int((datetime.now() + timedelta(days=30)).timestamp())
        payload = {
            "sub": str(account.id),
            "iss": "llmops",
            "exp": expire_at,
        }
        access_token = self.jwt_service.generate_token(payload)

        return {
            "expire_at": expire_at,
            "access_token": access_token,
        }
