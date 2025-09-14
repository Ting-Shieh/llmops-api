#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/9 下午3:47
@Author : zsting29@gmail.com
@File   : full_text_retriever.py
"""
from collections import Counter
from typing import List
from uuid import UUID

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.pydantic_v1 import Field
from langchain_core.retrievers import BaseRetriever

from internal.model import KeywordTable, Segment
from internal.service import JiebaService
from pkg.sqlalchemy import SQLAlchemy


class FullTextRetriever(BaseRetriever):
    """全文檢索器"""
    db: SQLAlchemy
    dataset_ids: list[UUID]
    jieba_service: JiebaService
    search_kwargs: dict = Field(default_factory=dict)

    def _get_relevant_documents(
            self,
            query: str,
            *,
            run_manager: CallbackManagerForRetrieverRun,
    ) -> List[LCDocument]:
        """根據傳遞的query執行關鍵字檢索獲取LangChain文件列表"""
        # 1.將查詢query轉換成關鍵字列表
        keywords = self.jieba_service.extract_keywords(query, 10)

        # 2.尋找指定知識庫的關鍵字表
        keyword_tables = [
            keyword_table for keyword_table, in
            self.db.session.query(KeywordTable).with_entities(KeywordTable.keyword_table).filter(
                KeywordTable.dataset_id.in_(self.dataset_ids)
            ).all()
        ]

        # 3.遍歷所有的知識庫關鍵字表，找到匹配query關鍵字的id列表
        all_ids = []
        for keyword_table in keyword_tables:
            # 4.遍歷每一個關鍵字表的每一項
            for keyword, segment_ids in keyword_table.items():
                # 5.如果數據存在則提取關鍵字對應的片段id列表
                if keyword in keywords:
                    all_ids.extend(segment_ids)

        # 6.統計segment_id出現的頻率，這裡可以使用Counter進行快速統計
        id_counter = Counter(all_ids)

        # 7.獲取頻率最高的前k條數據，格式為[(segment_id, freq), (segment_id, freq), ...]
        k = self.search_kwargs.get("k", 4)
        top_k_ids = id_counter.most_common(k)

        # 8.根據得到的id列表檢索資料庫得到片段列表資訊
        segments = self.db.session.query(Segment).filter(
            Segment.id.in_([id for id, _ in top_k_ids])
        ).all()
        segment_dict = {
            str(segment.id): segment for segment in segments
        }

        # 9.根據頻率進行排序
        sorted_segments = [segment_dict[str(id)] for id, freq in top_k_ids if id in segment_dict]

        # 10.構建LangChain文件列表
        lc_documents = [LCDocument(
            page_content=segment.content,
            metadata={
                "account_id": str(segment.account_id),
                "dataset_id": str(segment.dataset_id),
                "document_id": str(segment.document_id),
                "segment_id": str(segment.id),
                "node_id": str(segment.node_id),
                "document_enabled": True,
                "segment_enabled": True,
                "score": 0,
            }
        ) for segment in sorted_segments]

        return lc_documents
