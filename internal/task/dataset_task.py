#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/14 下午7:35
@Author : zsting29@gmail.com
@File   : dataset_task.py
"""
from uuid import UUID

from celery import shared_task


@shared_task
def delete_dataset(dataset_id: UUID) -> None:
    """根據傳遞的知識庫id刪除特定的知識庫資訊"""
    from app.http.module import injector
    from internal.service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.delete_dataset(dataset_id)
