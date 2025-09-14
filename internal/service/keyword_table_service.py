#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/6 下午4:53
@Author : zsting29@gmail.com
@File   : keyword_table_service.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from redis import Redis

from internal.entity.cache_entity import LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE, LOCK_EXPIRE_TIME
from internal.model import KeywordTable, Segment
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class KeywordTableService(BaseService):
    """知識庫關鍵字表服務"""
    db: SQLAlchemy
    redis_client: Redis

    def get_keyword_table_from_dataset_id(self, dataset_id: UUID) -> KeywordTable:
        """根據傳遞的知識庫id獲取關鍵字表"""
        keyword_table = self.db.session.query(KeywordTable).filter(
            KeywordTable.dataset_id == dataset_id,
        ).one_or_none()
        if keyword_table is None:
            keyword_table = self.create(KeywordTable, dataset_id=dataset_id, keyword_table={})

        return keyword_table

    def delete_keyword_table_from_ids(self, dataset_id: UUID, segment_ids: list[UUID]) -> None:
        """根據傳遞的知識庫id+片段id列表刪除對應關鍵字表中多餘的數據"""
        # 1.刪除知識庫關鍵字表裡多餘的數據，該操作需要上鎖，避免在並發的情況下拿到錯誤的數據
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(dataset_id=dataset_id)
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE_TIME):
            # 2.獲取當前知識庫的關鍵字表
            keyword_table_record = self.get_keyword_table_from_dataset_id(dataset_id)
            keyword_table = keyword_table_record.keyword_table.copy()  # 創建新的引用

            # 3.將片段id列錶轉換成集合，並創建關鍵字集合用於清除空關鍵字
            segment_ids_to_delete = set([str(segment_id) for segment_id in segment_ids])
            keywords_to_delete = set()

            # 4.循環遍歷所有關鍵字執行判斷與更新
            for keyword, ids in keyword_table.items():
                ids_set = set(ids)
                if segment_ids_to_delete.intersection(ids_set):
                    keyword_table[keyword] = list(ids_set.difference(segment_ids_to_delete))
                    if not keyword_table[keyword]:
                        keywords_to_delete.add(keyword)

            # 5.檢測空關鍵字數據並刪除（關鍵字並沒有映射任何欄位id的數據）
            for keyword in keywords_to_delete:
                del keyword_table[keyword]

            # 6.將數據更新到關鍵字表中
            self.update(keyword_table_record, keyword_table=keyword_table)  # 確保每此都會更新

    def add_keyword_table_from_ids(self, dataset_id: UUID, segment_ids: list[UUID]) -> None:
        """根據傳遞的知識庫id+片段id列表，在關鍵字表中添加關鍵字"""
        # 1.新增知識庫關鍵字表裡多餘的數據，該操作需要上鎖，避免在並發的情況下拿到錯誤的數據
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(dataset_id=dataset_id)
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE_TIME):
            # 2.獲取指定知識庫的關鍵字詞表
            keyword_table_record = self.get_keyword_table_from_dataset_id(dataset_id)
            keyword_table = {
                field: set(value) for field, value in keyword_table_record.keyword_table.items()
            }

            # 3.根據segment_ids尋找片段的關鍵字資訊
            segments = self.db.session.query(Segment).with_entities(Segment.id, Segment.keywords).filter(
                Segment.id.in_(segment_ids),
            ).all()
            # 4.循環將新關鍵字添加到關鍵字表中
            for id, keywords in segments:
                for keyword in keywords:
                    if keyword not in keyword_table:
                        keyword_table[keyword] = set()
                    keyword_table[keyword].add(str(id))

            # 5.更新關鍵字表
            self.update(
                keyword_table_record,
                keyword_table={field: list(value) for field, value in keyword_table.items()}
            )
