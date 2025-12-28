#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:33
@Author : zsting29@gmail.com
@File   : start_node.py
"""
import time
from typing import Optional

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.variable_entity import VARIABLE_TYPE_DEFAULT_VALUE_MAP
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.exception import FailException
from .start_entity import StartNodeData


class StartNode(BaseNode):
    """開始節點"""
    node_data: StartNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """開始節點執行函數，該函數會提取狀態中的輸入資訊並生成節點結果"""
        # 1.提取節點數據中的輸入數據
        start_at = time.perf_counter()
        inputs = self.node_data.inputs

        # 2.循環遍歷輸入數據，並提取需要的數據，同時檢測必填的數據是否傳遞，如果未傳遞則直接報錯
        outputs = {}
        for input in inputs:
            input_value = state["inputs"].get(input.name, None)

            # 3.檢測欄位是否必填，如果是則檢測是否賦值
            if input_value is None:
                if input.required:
                    raise FailException(f"工作流參數生成出錯，{input.name}為必填參數")
                else:
                    input_value = VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(input.type)

            # 4.提取出輸出數據
            outputs[input.name] = input_value

        # 5.構建狀態數據並返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=state["inputs"],
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
