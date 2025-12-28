#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:37
@Author : zsting29@gmail.com
@File   : template_transform_node.py
"""
import time
from typing import Optional

from jinja2 import Template
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .template_transform_entity import TemplateTransformNodeData


class TemplateTransformNode(BaseNode):
    """模板轉換節點，將多個變數資訊合併成一個"""
    node_data: TemplateTransformNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """模板轉換節點執行函數，將傳遞的多個變數合併成字串後返回"""
        # 1.提取節點中的輸入數據
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 2.使用jinja2格式模板資訊
        template = Template(self.node_data.template)
        template_value = template.render(**inputs_dict)

        # 3.提取並構建輸出數據結構
        outputs = {"output": template_value}

        # 4.構建響應狀態並返回
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
