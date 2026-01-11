#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/1/6 下午8:34
@Author : zsting29@gmail.com
@File   : app_task.py
"""
from uuid import UUID

from celery import shared_task


@shared_task
def auto_create_app(
        name: str,
        description: str,
        account_id: UUID,
) -> None:
    """根據傳遞的名稱、描述、帳號id創建一個Agent"""
    from app.http.module import injector
    from internal.service import AppService

    app_service = injector.get(AppService)
    app_service.auto_create_app(name, description, account_id)
