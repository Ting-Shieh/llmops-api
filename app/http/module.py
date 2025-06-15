#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/13 下午9:54
@Author : zsting29@gmail.com
@File   : module.py
"""
from flask_migrate import Migrate
from injector import Binder, Module, Injector
from redis import Redis

from internal.extension.database_extension import db
from internal.extension.migrate_extension import migrate
from internal.extension.redis_extension import redis_client
from pkg.sqlalchemy import SQLAlchemy


class ExtensionModule(Module):
    """擴展模塊的依賴注入"""

    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
        binder.bind(Redis, to=redis_client)


injector = Injector([ExtensionModule])
