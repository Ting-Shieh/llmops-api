#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:35
@Author : zsting29@gmail.com
@File   : llm_node.py
"""
import time
from typing import Optional

from jinja2 import Template
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .llm_entity import LLMNodeData


class LLMNode(BaseNode):
    """大語言模型節點"""
    node_data: LLMNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """大語言模型節點調用工具，根據輸入欄位+預設prompt生成對應內容後輸出"""
        # 1.提取節點中的輸入數據
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 2.使用jinja2格式模板資訊
        template = Template(self.node_data.prompt)
        prompt_value = template.render(**inputs_dict)

        # 3.透過依賴管理器獲取language_model_service並載入模型
        from app.http.module import injector
        from internal.service import LanguageModelService

        language_model_service = injector.get(LanguageModelService)
        llm = language_model_service.load_language_model(self.node_data.language_model_config)

        # 4.使用stream來代替invoke，避免介面長時間未響應超時
        content = ""
        for chunk in llm.stream(prompt_value):
            content += chunk.content

        # 5.提取並構建輸出數據結構
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = content
        else:
            outputs["output"] = content

        # 6.構建響應狀態並返回
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
