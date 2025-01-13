#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/28 下午5:41
@Author : zsting29@gmail.com
@File   : config.py
"""
import os
from typing import Any

from config.default_config import DEFAULT_CONFIG


def _get_env(key: str) -> Any:
    """從環境變量中獲取配置項，如果找不到則返回默認值"""
    return os.getenv(key, DEFAULT_CONFIG.get(key))


def _get_bool_env(key: str) -> Any:
    """從環境變量中獲取bool type配置項，如果找不到則返回默認值"""
    val: str = _get_env(key)
    return val.lower() == "true" if val is not None else False


class Config:
    def __init__(self):
        # 關閉 wtf 的 csrf 保護
        self.WTF_CSRF_ENABLED = _get_bool_env("WTF_CSRF_ENABLED")

        # DB 配置
        self.SQLALCHEMY_DATABASE_URI = _get_env("SQLALCHEMY_DATABASE_URI")
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": int(_get_env("SQLALCHEMY_POOL_SIZE")),
            "pool_recycle": int(_get_env("SQLALCHEMY_POOL_RECYCLE")),
        }
        self.SQLALCHEMY_ECHO = _get_bool_env("SQLALCHEMY_ECHO")
