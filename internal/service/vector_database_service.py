#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/23 下午6:58
@Author : zsting29@gmail.com
@File   : vector_database_service.py
"""
import os

import weaviate
from injector import inject
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_weaviate import WeaviateVectorStore
from weaviate.client import WeaviateClient

from internal.service import EmbeddingsService


@inject
class VectorDatabaseService:
    """向量數據庫服務"""
    client: WeaviateClient
    vector_store: WeaviateVectorStore
    embeddings_service: EmbeddingsService

    def __init__(self, embeddings_service: EmbeddingsService):
        # 賦值embeddings_service
        self.embeddings_service = embeddings_service

        # create and connect Weaviate Vector DB
        # cluster_url = os.getenv("WEAVIATE_URL")
        # api_key = os.getenv("WEAVIATE_API_KEY")
        # print(f"Connecting to Weaviate at {cluster_url} with API key {api_key[:10]}...")  # 仅打印前 10 个字符的 API 密钥

        # local
        self.client = weaviate.connect_to_local(
            host=os.getenv("WEAVIATE_HOST"),
            port=int(os.getenv("WEAVIATE_PORT"))
        )

        # # 雲的
        # self.client = weaviate.connect_to_weaviate_cloud(
        #     cluster_url=os.getenv("WEAVIATE_URL"),
        #     auth_credentials=Auth.api_key(os.getenv("WEAVIATE_API_KEY"))
        # )

        # create LangChain Vector DB
        self.vector_store = WeaviateVectorStore(
            client=self.client,
            index_name="Dataset",
            text_key="text",
            embedding=self.embeddings_service.embeddings
            # 使用本地 -> 非本地 OpenAIEmbeddings(model="text-embedding-3-small")
        )

    def get_retriever(self) -> VectorStoreRetriever:
        """獲取檢索器"""
        return self.vector_store.as_retriever()

    @classmethod
    def combine_documents(cls, documents: list[Document]) -> str:
        """將對應的文檔列表使用換行符進行合併"""
        return "\n\n".join([document.page_content for document in documents])
