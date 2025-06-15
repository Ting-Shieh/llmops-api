#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/15 下午3:35
@Author : zsting29@gmail.com
@File   : redis_extension.py
"""
import redis
from flask import Flask
from redis import Connection, SSLConnection

redis_client = redis.Redis()


def init_app(app: Flask):
    """初始化redis客戶端"""
    # 1.檢測不同的場景使用不同的連接方式
    connection_class = Connection
    if app.config.get("REDIS_USE_SSL", False):
        connection_class = SSLConnection

    # 2.創建redis連接池
    redis_client.connection_pool = redis.ConnectionPool(**{
        "host": app.config.get("REDIS_HOST", "127.0.0.1"),
        "port": app.config.get("REDIS_PORT", 6379),
        "username": app.config.get("REDIS_USERNAME", None),
        "password": app.config.get("REDIS_PASSWORD", None),
        "db": app.config.get("REDIS_DB", 0),
        "encoding": "utf-8",
        "encoding_errors": "strict",
        "decode_responses": False,
    }, connection_class=connection_class)

    app.extensions["redis"] = redis_client
