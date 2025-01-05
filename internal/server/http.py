#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午3:08
@Author : zsting29@gmail.com
@File   : http.py
"""
import os

from flask import Flask

from config import Config
from internal.exception import CustomException
from internal.router import Router
from pkg.response import Response, json, HttpCode


class Http(Flask):
    """Http服務引擎"""

    def __init__(self, *args, conf: Config, router: Router, **kwargs):
        super().__init__(*args, **kwargs)
        # 註冊應用路由
        router.register_router(self)

        # 註冊綁定異常錯誤處理
        self.register_error_handler(Exception, self._register_error_handler)

        self.config.from_object(conf)

    def _register_error_handler(self, error: Exception):
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
