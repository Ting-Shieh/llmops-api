#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午3:59
@Author : zsting29@gmail.com
@File   : app.py
"""
import dotenv
from injector import Injector

from config import Config
from internal.router import Router
from internal.server import Http

# 將.env 加載到環境變量中
dotenv.load_dotenv()

conf = Config()

injector = Injector()
app = Http(__name__, conf=conf, router=injector.get(Router))

if __name__ == "__main__":
    app.run(debug=True)
