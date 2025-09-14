#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/9 下午3:43
@Author : zsting29@gmail.com
@File   : semantic_retriever.py
"""
from typing import List
from uuid import UUID

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.pydantic_v1 import Field
from langchain_core.retrievers import BaseRetriever
from langchain_weaviate import WeaviateVectorStore
from weaviate.classes.query import Filter


class SemanticRetriever(BaseRetriever):
    """相似性檢索器/向量檢索器"""
    dataset_ids: list[UUID]
    vector_store: WeaviateVectorStore
    search_kwargs: dict = Field(default_factory=dict)

    def _get_relevant_documents(
            self,
            query: str,
            *,
            run_manager: CallbackManagerForRetrieverRun,
    ) -> List[LCDocument]:
        """根據傳遞的query執行相似性檢索"""
        # 1.提取最大搜索條件k，預設值為4
        k = self.search_kwargs.pop("k", 4)

        # 2.執行相似性檢索並獲取得分資訊
        search_result = self.vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            **{
                # 所有條件均需要滿足
                "filters": Filter.all_of([
                    Filter.by_property("dataset_id").contains_any([str(dataset_id) for dataset_id in self.dataset_ids]),
                    Filter.by_property("document_enabled").equal(True),
                    Filter.by_property("segment_enabled").equal(True),
                ]),
                **self.search_kwargs,
            }
        )
        if search_result is None or len(search_result) == 0:
            return []
        lc_documents, scores = zip(*search_result)

        # 3.執行循環將得分添加到文件元數據中
        for lc_document, score in zip(lc_documents, scores):
            lc_document.metadata["score"] = score

        return list(lc_documents)
