#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/13 下午3:38
@Author : zsting29@gmail.com
@File   : logging_extension.py
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from flask import Flask


def init_app(app: Flask):
    """日誌記錄器初始化"""
    # 1.設置日誌儲存資料夾，若不存在則創建
    logging_folder = os.path.join(os.getcwd(), 'storage', 'log')
    if not os.path.exists(logging_folder):
        os.makedirs(logging_folder)

    # 2.定義日誌文件名
    logging_file = os.path.join(logging_folder, 'app.log')

    # 3.設置日誌格式，並讓日誌每日更新
    handler = TimedRotatingFileHandler(
        logging_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    # 4.在開發環境下同時將日誌輸出到控制台
    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s]: %(message)s"
    )
    if app.debug or os.getenv("FLASK_ENV") == "development":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
    # handler.setLevel(logging.DEBUG if app.debug or os.getenv("FLASK_ENV") == "development" else logging.WARNING)
    # handler.setFormatter(formatter)
    # logging.getLogger().addHandler(handler)

    # 5.
    pass
