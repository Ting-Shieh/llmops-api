#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/5 下午4:10
@Author : zsting29@gmail.com
@File   : document_task.py
"""
from uuid import UUID

from celery import shared_task


@shared_task
def build_documents(document_ids: list[UUID]) -> None:
    """根據傳遞的文件id列表，構建文件"""
    from app.http.module import injector
    from internal.service.indexing_service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.build_documents(document_ids)


@shared_task
def update_document_enabled(document_id: UUID) -> None:
    """根據傳遞的文件id修改文件的狀態"""
    from app.http.module import injector
    from internal.service.indexing_service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.update_document_enabled(document_id)


@shared_task
def delete_document(dataset_id: UUID, document_id: UUID) -> None:
    """根據傳遞的文件id+知識庫id清除文件記錄"""
    from app.http.module import injector
    from internal.service.indexing_service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.delete_document(dataset_id, document_id)
