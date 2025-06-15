#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/13 下午9:23
@Author : zsting29@gmail.com
@File   : default_config.py
"""
# 應用默認配置項
DEFAULT_CONFIG = {
    "WTF_CSRF_ENABLED": "False",
    "SQLALCHEMY_DATABASE_URI": "",
    "SQLALCHEMY_POOL_SIZE": 30,
    "SQLALCHEMY_POOL_RECYCLE": 3600,
    "SQLALCHEMY_ECHO": "True",

    # Redis
    "REDIS_HOST": "127.0.0.1",
    "REDIS_PORT": "6379",
    "REDIS_USERNAME": "",
    "REDIS_PASSWORD": "",
    "REDIS_DB": "0",
    "REDIS_USE_SSL": "False",
}
