#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:39
@Author : zsting29@gmail.com
@File   : dataset_retrieval_node.py
"""
import time
from typing import Optional, Any
from uuid import UUID

from flask import Flask
from langchain_core.pydantic_v1 import PrivateAttr
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .dataset_retrieval_entity import DatasetRetrievalNodeData


class DatasetRetrievalNode(BaseNode):
    """知識庫檢索節點"""
    node_data: DatasetRetrievalNodeData
    _retrieval_tool: BaseTool = PrivateAttr(None)

    def __init__(
            self,
            *args: Any,
            flask_app: Flask,
            account_id: UUID,
            **kwargs: Any,
    ):
        """構造函數，完成知識庫檢索節點的初始化"""
        # 1.調用父類構造函數完成數據初始化
        super().__init__(*args, **kwargs)

        # 2.導入依賴注入及檢索服務
        from app.http.module import injector
        from internal.service import RetrievalService

        retrieval_service = injector.get(RetrievalService)

        # 3.構建檢索服務工具
        self._retrieval_tool = retrieval_service.create_langchain_tool_from_search(
            flask_app=flask_app,
            dataset_ids=self.node_data.dataset_ids,
            account_id=account_id,
            **self.node_data.retrieval_config.dict(),
        )

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """知識庫檢索節點調用函數，執行響應的知識庫檢索後返回"""
        # 1.提取節點輸入變數字典映射
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 2.調用知識庫檢索工具
        combine_documents = self._retrieval_tool.invoke(inputs_dict)

        # 3.提取並構建輸出數據結構
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = combine_documents
        else:
            outputs["combine_documents"] = combine_documents

        # 4.返迴響應狀態
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
