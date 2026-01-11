#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/1/6 下午8:32
@Author : zsting29@gmail.com
@File   : faiss_service.py
"""
import os

from injector import inject
from langchain_community.vectorstores import FAISS
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool, tool

from internal.core.agent.entities.agent_entity import DATASET_RETRIEVAL_TOOL_NAME
from internal.lib.helper import combine_documents
from .embeddings_service import EmbeddingsService


@inject
class FaissService:
    """Faiss向量資料庫服務"""
    faiss: FAISS
    embeddings_service: EmbeddingsService

    def __init__(self, embeddings_service: EmbeddingsService):
        """構造函數，完成Faiss向量資料庫的初始化"""
        # 1.賦值embeddings_service
        self.embeddings_service = embeddings_service

        # 2.獲取internal路徑並計算本地向量資料庫的實際路徑
        internal_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        faiss_vector_store_path = os.path.join(internal_path, "core", "vector_store")

        # 3.初始化faiss向量資料庫
        self.faiss = FAISS.load_local(
            folder_path=faiss_vector_store_path,
            embeddings=self.embeddings_service.embeddings,
            allow_dangerous_deserialization=True,
        )

    def convert_faiss_to_tool(self) -> BaseTool:
        """將Faiss向量資料庫檢索器轉換成LangChain工具"""
        # 1.將Faiss向量資料庫轉換成檢索器
        retrieval = self.faiss.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20},
        )

        # 2.構建檢索鏈，並將檢索的結果合併成字串
        search_chain = retrieval | combine_documents

        class DatasetRetrievalInput(BaseModel):
            """知識庫檢索工具輸入結構"""
            query: str = Field(description="知識庫檢索query語句，類型為字串")

        @tool(DATASET_RETRIEVAL_TOOL_NAME, args_schema=DatasetRetrievalInput)
        def dataset_retrieval(query: str) -> str:
            """如果需要檢索擴展的知識庫內容，當你覺得用戶的提問超過你的知識範圍時，可以嘗試調用該工具，輸入為搜索query語句，返回數據為檢索內容字串"""
            return search_chain.invoke(query)

        return dataset_retrieval
