#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午3:08
@Author : zsting29@gmail.com
@File   : http.py
"""
import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from config import Config
from internal.exception import CustomException
from internal.extension import logging_extension
from internal.router import Router
from pkg.response import Response, json, HttpCode
from pkg.sqlalchemy import SQLAlchemy


class Http(Flask):
    """Http服務引擎"""

    def __init__(
            self,
            *args,
            conf: Config,
            db: SQLAlchemy,
            migrate: Migrate,
            router: Router,
            **kwargs
    ):
        # 調用父類構造函數初始化
        super().__init__(*args, **kwargs)

        # 初始化應用配置
        self.config.from_object(conf)

        # 註冊綁定異常錯誤處理
        self.register_error_handler(Exception, self._register_error_handler)

        # 初始化Flask 擴展
        db.init_app(self)
        migrate.init_app(self, db, directory='internal/migration')
        logging_extension.init_app(self)
        # with self.app_context():
        #     _ = App()
        #     db.create_all()

        # CORS
        CORS(self, resources={
            r"/*": {
                "origins": "*",
                "supports_credentials": True,
                # # 以下可以不用配置
                # "methods": ["GET", "POST"],
                # "allow_headers": ["Content-Type"],
            }
        })

        # 註冊應用路由
        router.register_router(self)

    def _register_error_handler(self, error: Exception):
        # 日誌路異常訊息
        logging.error("An error occurred: %s", error, exc_info=True)
        #  異常訊息是否為自定義異常，若是則可提取message & code訊息．
        if isinstance(error, CustomException):
            return json(Response(
                code=error.code,
                message=error.message,
                data=error.data if error.data is not None else {}
            ))
        # 若非為自定義異常，則可能為程序或數據庫所拋出的異常，也可以提取訊息並拋出FAIL
        if self.debug or os.getenv("FLASK_ENV") == "development":
            raise error
        else:
            return json(Response(
                code=HttpCode.FAIL,
                message=str(error),
                data={}
            ))
