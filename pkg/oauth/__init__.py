#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/12 下午2:25
@Author : zsting29@gmail.com
@File   : __init__.py.py
"""
from .github_oauth import GithubOAuth
from .oauth import OAuthUserInfo, OAuth

__all__ = [
    "OAuthUserInfo",
    "OAuth",
    "GithubOAuth"
]
