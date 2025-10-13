#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/12 下午1:26
@Author : zsting29@gmail.com
@File   : jwt_service.py
"""
import os
from dataclasses import dataclass
from typing import Any

import jwt
from injector import inject

from internal.exception import UnauthorizedException


@inject
@dataclass
class JwtService:
    """jwt服務"""

    @classmethod
    def generate_token(cls, payload: dict[str, Any]) -> str:
        """根據傳遞的載荷資訊生成token資訊"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @classmethod
    def parse_token(cls, token: str) -> dict[str, Any]:
        """解析傳入的token資訊得到載荷"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("授權認證憑證已過期請重新登入")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("解析token出錯，請重新登入")
        except Exception as e:
            raise UnauthorizedException(str(e))
