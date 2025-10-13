#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/12 下午1:33
@Author : zsting29@gmail.com
@File   : account_service.py
"""
import base64
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from flask import request
from injector import inject

from internal.exception import FailException
from internal.model import Account, AccountOAuth
from pkg.password import compare_password, hash_password
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService  # 改為相對導入
from .jwt_service import JwtService


@inject
@dataclass
class AccountService(BaseService):
    """帳號服務"""
    db: SQLAlchemy
    jwt_service: JwtService

    def get_account(self, account_id: UUID) -> Account:
        """根據id獲取指定的帳號模型"""
        return self.get(Account, account_id)

    def get_account_oauth_by_provider_name_and_openid(
            self,
            provider_name: str,
            openid: str,
    ) -> AccountOAuth:
        """根據傳遞的提供者名字+openid獲取第三方授權認證記錄"""
        return self.db.session.query(AccountOAuth).filter(
            AccountOAuth.provider == provider_name,
            AccountOAuth.openid == openid,
        ).one_or_none()

    def get_account_by_email(self, email: str) -> Account:
        """根據傳遞的信箱查詢帳號資訊"""
        return self.db.session.query(Account).filter(
            Account.email == email,
        ).one_or_none()

    def create_account(self, **kwargs) -> Account:
        """根據傳遞的鍵值對創建帳號資訊"""
        return self.create(Account, **kwargs)

    def update_password(self, password: str, account: Account) -> Account:
        """更新當前帳號密碼資訊"""
        # 1.生成密碼隨機鹽值
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()

        # 2.利用鹽值和password進行加密
        password_hashed = hash_password(password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()

        # 3.更新帳號資訊
        self.update_account(account, password=base64_password_hashed, password_salt=base64_salt)

        return account

    def update_account(self, account: Account, **kwargs) -> Account:
        """根據傳遞的資訊更新帳號"""
        self.update(account, **kwargs)
        return account

    def password_login(self, email: str, password: str) -> dict[str, Any]:
        """根據傳遞的密碼+信箱登入特定的帳號"""
        # 1.根據傳遞的信箱查詢帳號是否存在
        account = self.get_account_by_email(email)
        if not account:
            raise FailException("帳號不存在或者密碼錯誤，請核實後重試")

        # 2.校驗帳號密碼是否正確
        if not account.is_password_set or not compare_password(
                password,
                account.password,
                account.password_salt,
        ):
            raise FailException("帳號不存在或者密碼錯誤，請核實後重試")

        # 3.生成憑證資訊
        expire_at = int((datetime.now() + timedelta(days=30)).timestamp())
        payload = {
            "sub": str(account.id),
            "iss": "llmops",
            "exp": expire_at,
        }
        access_token = self.jwt_service.generate_token(payload)

        # 4.更新帳號的登入資訊
        self.update(
            account,
            last_login_at=datetime.now(),
            last_login_ip=request.remote_addr,
        )

        return {
            "expire_at": expire_at,
            "access_token": access_token,
        }
