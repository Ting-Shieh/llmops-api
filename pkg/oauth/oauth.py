#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/12 下午2:25
@Author : zsting29@gmail.com
@File   : oauth.py
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    """OAuth用戶基礎資訊，只記錄id/name/email"""
    id: str
    name: str
    email: str


@dataclass
class OAuth(ABC):
    """第三方OAuth授權認證基礎類"""
    client_id: str  # 用戶端id
    client_secret: str  # 用戶端秘鑰
    redirect_uri: str  # 重定向uri

    @abstractmethod
    def get_provider(self) -> str:
        """獲取服務提供者對應的名字"""
        pass

    @abstractmethod
    def get_authorization_url(self) -> str:
        """獲取跳轉授權認證的URL地址"""
        pass

    @abstractmethod
    def get_access_token(self, code: str) -> str:
        """根據傳入的code代碼獲取授權令牌"""
        pass

    @abstractmethod
    def get_raw_user_info(self, token: str) -> dict:
        """根據傳入的token獲取OAuth原始資訊"""
        pass

    def get_user_info(self, token: str) -> OAuthUserInfo:
        """根據傳入的token獲取OAuthUserInfo資訊"""
        raw_info = self.get_raw_user_info(token)
        return self._transform_user_info(raw_info)

    @abstractmethod
    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        """將OAuth原始資訊轉換成OAuthUserInfo"""
        pass
