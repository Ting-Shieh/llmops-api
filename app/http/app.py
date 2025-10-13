#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午3:59
@Author : zsting29@gmail.com
@File   : main.py
"""
import dotenv
from flask_login import LoginManager
from flask_migrate import Migrate

from app.http.module import injector
from config import Config
from internal.middleware.middleware import Middleware
from internal.router import Router
from internal.server import Http
from pkg.sqlalchemy import SQLAlchemy

# 將.env 加載到環境變量中
dotenv.load_dotenv()

conf = Config()

app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    login_manager=injector.get(LoginManager),
    middleware=injector.get(Middleware),
    router=injector.get(Router)
)
celery = app.extensions["celery"]
