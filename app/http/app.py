#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午3:59
@Author : zsting29@gmail.com
@File   : app.py
"""
from injector import Injector

from internal.router import Router
from internal.server import Http

injector = Injector()
app = Http(__name__, router=injector.get(Router))

if __name__ == "__main__":
    app.run(debug=True)
