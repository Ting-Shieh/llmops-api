#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午3:08
@Author : zsting29@gmail.com
@File   : http.py
"""
from flask import Flask

from internal.router import Router


class Http(Flask):
    """Http服務引擎"""

    def __init__(self, *args, router: Router, **kwargs):
        super().__init__(*args, **kwargs)
        # 註冊應用路由
        router.register_router(self)
