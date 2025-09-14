#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/9 下午3:37
@Author : zsting29@gmail.com
@File   : retrieval_service.py
"""

from dataclasses import dataclass
from uuid import UUID

from injector import inject
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document as LCDocument
from sqlalchemy import update

from internal.entity.dataset_entity import RetrievalStrategy, RetrievalSource
from internal.exception import NotFoundException
from internal.model import Segment, Dataset, DatasetQuery
from .base_service import BaseService
from .vector_database_service import VectorDatabaseService
from pkg.sqlalchemy import SQLAlchemy
from .jieba_service import JiebaService


@inject
@dataclass
class RetrievalService(BaseService):
    """檢索服務"""
    db: SQLAlchemy
    jieba_service: JiebaService
    vector_database_service: VectorDatabaseService

    def search_in_datasets(
            self,
            dataset_ids: list[UUID],
            query: str,
            account_id: UUID,
            retrieval_strategy: str = RetrievalStrategy.SEMANTIC,
            k: int = 4,
            score: float = 0,
            retrival_source: str = RetrievalSource.HIT_TESTING,
    ) -> list[LCDocument]:
        """根據傳遞的query+知識庫列表執行檢索，並返回檢索的文件+得分數據（如果檢索策略為全文檢索，則得分為0）"""
        # 1.提取知識庫列表並校驗權限同時更新知識庫id
        datasets = self.db.session.query(Dataset).filter(
            Dataset.id.in_(dataset_ids),
            Dataset.account_id == account_id
        ).all()
        if datasets is None or len(datasets) == 0:
            raise NotFoundException("當前無知識庫可執行檢索")
        dataset_ids = [dataset.id for dataset in datasets]

        # 2.構建不同種類的檢索器
        from internal.core.retrievers import SemanticRetriever, FullTextRetriever
        semantic_retriever = SemanticRetriever(
            dataset_ids=dataset_ids,
            vector_store=self.vector_database_service.vector_store,
            search_kwargs={
                "k": k,
                "score_threshold": score,
            },
        )
        full_text_retriever = FullTextRetriever(
            db=self.db,
            dataset_ids=dataset_ids,
            jieba_service=self.jieba_service,
            search_kwargs={
                "k": k
            },
        )
        hybrid_retriever = EnsembleRetriever(
            retrievers=[semantic_retriever, full_text_retriever],
            weights=[0.5, 0.5],
        )

        # 3.根據不同的檢索策略執行檢索
        if retrieval_strategy == RetrievalStrategy.SEMANTIC:
            lc_documents = semantic_retriever.invoke(query)[:k]
        elif retrieval_strategy == RetrievalStrategy.FULL_TEXT:
            lc_documents = full_text_retriever.invoke(query)[:k]
        else:
            lc_documents = hybrid_retriever.invoke(query)[:k]

        # 4.添加知識庫查詢記錄（只儲存唯一記錄，也就是一個知識庫如果檢索了多篇文件，也只儲存一條）
        unique_dataset_ids = list(set(str(lc_document.metadata["dataset_id"]) for lc_document in lc_documents))
        for dataset_id in unique_dataset_ids:
            self.create(
                DatasetQuery,
                dataset_id=dataset_id,
                query=query,
                source=retrival_source,
                # todo:等待APP配置模組完成後進行調整
                source_app_id=None,
                created_by=account_id,
            )

        # 5.批次更新片段的命中次數，召回次數，涵蓋了構建+執行語句
        with self.db.auto_commit():
            stmt = (
                update(Segment)
                .where(Segment.id.in_([lc_document.metadata["segment_id"] for lc_document in lc_documents]))
                .values(hit_count=Segment.hit_count + 1)
            )
            self.db.session.execute(stmt)

        return lc_documents
