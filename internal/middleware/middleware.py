#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/12 下午1:28
@Author : zsting29@gmail.com
@File   : middleware.py
"""
from dataclasses import dataclass
from typing import Optional

from flask import Request
from injector import inject

from internal.exception import UnauthorizedException
from internal.model import Account
from internal.service import ApiKeyService
from internal.service.account_service import AccountService
from internal.service.jwt_service import JwtService


@inject
@dataclass
class Middleware:
    """應用中間件，可以重寫request_loader與unauthorized_handler"""
    jwt_service: JwtService
    api_key_service: ApiKeyService
    account_service: AccountService

    def request_loader(self, request: Request) -> Optional[Account]:
        """登錄管理器的請求載入器"""
        # 1.單獨為llmops路由藍圖創建請求載入器
        if request.blueprint == "llmops":
            # 2.校驗獲取access_token
            access_token = self._validate_credential(request)

            # 3.解析token資訊得到用戶資訊並返回
            payload = self.jwt_service.parse_token(access_token)
            account_id = payload.get("sub")
            account = self.account_service.get_account(account_id)
            if not account:
                raise UnauthorizedException("當前帳戶不存在，請重新登入")
            return account
        elif request.blueprint == "openapi":
            # 4.校驗獲取api_key
            api_key = self._validate_credential(request)

            # 5.解析得到APi秘鑰記錄
            api_key_record = self.api_key_service.get_api_by_by_credential(api_key)

            # 6.判斷Api秘鑰記錄是否存在，如果不存在則拋出錯誤
            if not api_key_record or not api_key_record.is_active:
                raise UnauthorizedException("該秘鑰不存在或未啟用")

            # 7.獲取秘鑰帳號資訊並返回
            return api_key_record.account
        else:
            return None

    @classmethod
    def _validate_credential(cls, request: Request) -> str:
        """校驗請求頭中的憑證資訊，涵蓋access_token和api_key"""
        # 1.提取請求頭headers中的資訊
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise UnauthorizedException("該介面需要授權才能訪問，請登錄後嘗試")

        # 2.請求資訊中沒有空格分隔符號，則驗證失敗，Authorization: Bearer access_token
        if " " not in auth_header:
            raise UnauthorizedException("該介面需要授權才能訪問，驗證格式失敗")

        # 4.分割授權資訊，必須符合Bearer access_token
        auth_schema, credential = auth_header.split(None, 1)
        if auth_schema.lower() != "bearer":
            raise UnauthorizedException("該介面需要授權才能訪問，驗證格式失敗")

        return credential
