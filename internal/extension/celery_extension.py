#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/15 下午7:57
@Author : zsting29@gmail.com
@File   : celery_extension.py
"""
from celery import Task, Celery
from flask import Flask


def init_app(app: Flask):
    """Celery Config 初始化"""

    class FlaskTask(Task):
        """定義FlaskTask，確保celery在Flask應用的上好文中運行，此可訪問Flask配置與ＤＢ等內容"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    # 1.創建celery應用並配置
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()

    # 2.將celery掛在到app的擴展中
    app.extensions["celery"] = celery_app
