#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/9 下午3:37
@Author : zsting29@gmail.com
@File   : retrieval_service.py
"""

from dataclasses import dataclass
from uuid import UUID

from flask import Flask
from injector import inject
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document as LCDocument
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool, tool
from sqlalchemy import update

from internal.entity.dataset_entity import RetrievalStrategy, RetrievalSource
from internal.exception import NotFoundException
from internal.model import Segment, Dataset, DatasetQuery
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .jieba_service import JiebaService
from .vector_database_service import VectorDatabaseService
from ..core.agent.entities.agent_entity import DATASET_RETRIEVAL_TOOL_NAME
from ..lib.helper import combine_documents


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

    def create_langchain_tool_from_search(
            self,
            flask_app: Flask,
            dataset_ids: list[UUID],
            account_id: UUID,
            retrieval_strategy: str = RetrievalStrategy.SEMANTIC,
            k: int = 4,
            score: float = 0,
            retrival_source: str = RetrievalSource.HIT_TESTING,
    ) -> BaseTool:
        """根據傳遞的參數構建一個LangChain知識庫搜索工具"""

        class DatasetRetrievalInput(BaseModel):
            """知識庫檢索工具輸入結構"""
            query: str = Field(description="知識庫搜索query語句，類型為字串")

        @tool(DATASET_RETRIEVAL_TOOL_NAME, args_schema=DatasetRetrievalInput)
        def dataset_retrieval(query: str) -> str:
            """如果需要搜索擴展的知識庫內容，當你覺得用戶的提問超過你的知識範圍時，可以嘗試調用該工具，輸入為搜索query語句，返回數據為檢索內容字串"""
            # 1.調用search_in_datasets檢索得到LangChain文件列表
            with flask_app.app_context():
                documents = self.search_in_datasets(
                    dataset_ids=dataset_ids,
                    query=query,
                    account_id=account_id,
                    retrieval_strategy=retrieval_strategy,
                    k=k,
                    score=score,
                    retrival_source=retrival_source,
                )

            # 2.將LangChain文件列錶轉換成字串後返回
            if len(documents) == 0:
                return "知識庫內沒有檢索到對應內容"

            return combine_documents(documents)

        return dataset_retrieval
