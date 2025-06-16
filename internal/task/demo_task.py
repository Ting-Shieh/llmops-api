#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/15 下午11:39
@Author : zsting29@gmail.com
@File   : demo_task.py
"""
import logging
import time
from uuid import UUID

from celery import shared_task
from flask import current_app


@shared_task
def demo_task(id: UUID) -> str:
    """test async task"""
    logging.info("Sleep 5 seconds")
    time.sleep(5)
    logging.info(f"id value: {id}")
    logging.info(f"Config Info: {current_app.config}")
    return "Test Celery"
