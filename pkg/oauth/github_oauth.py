#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/13 下午7:07
@Author : zsting29@gmail.com
@File   : github_oauth.py
"""
import urllib.parse

import requests

from .oauth import OAuth, OAuthUserInfo


class GithubOAuth(OAuth):
    """GithubOAuth第三方授權認證類"""
    _AUTHORIZE_URL = "https://github.com/login/oauth/authorize"  # 跳轉授權介面
    _ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # 獲取授權令牌介面
    _USER_INFO_URL = "https://api.github.com/user"  # 獲取用戶資訊介面
    _EMAIL_INFO_URL = "https://api.github.com/user/emails"  # 獲取用戶信箱介面

    def get_provider(self) -> str:
        return "github"

    def get_authorization_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",  # 只請求用戶的基本資訊
        }
        return f"{self._AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    def get_access_token(self, code: str) -> str:
        # 1.組裝請求數據
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Accept": "application/json"}

        # 2.發起post請求並獲取相應的數據
        resp = requests.post(self._ACCESS_TOKEN_URL, data=data, headers=headers)
        resp.raise_for_status()
        resp_json = resp.json()

        # 3.提取access_token對應的數據
        access_token = resp_json.get("access_token")
        if not access_token:
            raise ValueError(f"Github OAuth授權失敗: {resp_json}")

        return access_token

    def get_raw_user_info(self, token: str) -> dict:
        # 1.組裝請求數據
        headers = {"Authorization": f"token {token}"}

        # 2.發起get請求獲取用戶數據
        resp = requests.get(self._USER_INFO_URL, headers=headers)
        resp.raise_for_status()
        raw_info = resp.json()

        # 3.發起get請求獲取用戶信箱
        email_resp = requests.get(self._EMAIL_INFO_URL, headers=headers)
        email_resp.raise_for_status()
        email_info = email_resp.json()

        # 4.提取信箱數據
        primary_email = next((email for email in email_info if email.get("primary", None)), None)

        return {**raw_info, "email": primary_email.get("email", None)}

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        # 1.提取信箱，如果不存在設置一個默認信箱
        email = raw_info.get("email")
        if not email:
            email = f"{raw_info.get('id')}+{raw_info.get('login')}@user.no-reply@github.com"

        # 2.組裝數據
        return OAuthUserInfo(
            id=str(raw_info.get("id")),
            name=str(raw_info.get("name")),
            email=str(email),
        )
