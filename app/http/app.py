#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午3:59
@Author : zsting29@gmail.com
@File   : main.py
"""
import dotenv
from flask_migrate import Migrate

# from .module import injector
from app.http.module import injector
from config import Config
from internal.router import Router
from internal.server import Http
from pkg.sqlalchemy import SQLAlchemy

# from .module import ExtensionModule

# 將.env 加載到環境變量中
dotenv.load_dotenv()

conf = Config()

# injector = Injector([ExtensionModule])
app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    router=injector.get(Router)
)
celery = app.extensions["celery"]
# if __name__ == "__main__":
#     app.run(debug=True, port=5001)
