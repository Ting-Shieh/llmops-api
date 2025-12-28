#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:44
@Author : zsting29@gmail.com
@File   : http_request_node.py
"""
import time
from typing import Optional

import requests
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .http_request_entity import (
    HttpRequestInputType,
    HttpRequestMethod,
    HttpRequestNodeData,
)


class HttpRequestNode(BaseNode):
    """HTTP請求節點"""
    node_data: HttpRequestNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """HTTP請求節點調用函數，像指定的URL發起請求並獲取相應"""
        # 1.提取節點輸入變數字典
        start_at = time.perf_counter()
        _inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 2.提取數據，涵蓋params、headers、body的數據
        inputs_dict = {
            HttpRequestInputType.PARAMS: {},
            HttpRequestInputType.HEADERS: {},
            HttpRequestInputType.BODY: {}
        }
        for input in self.node_data.inputs:
            inputs_dict[input.meta.get("type")][input.name] = _inputs_dict.get(input.name)

        # 3.請求方法映射
        request_methods = {
            HttpRequestMethod.GET: requests.get,
            HttpRequestMethod.POST: requests.post,
            HttpRequestMethod.PUT: requests.put,
            HttpRequestMethod.PATCH: requests.patch,
            HttpRequestMethod.DELETE: requests.delete,
            HttpRequestMethod.HEAD: requests.head,
            HttpRequestMethod.OPTIONS: requests.options,
        }

        # 4.根據傳遞的method+url發起請求
        request_method = request_methods[self.node_data.method]
        if self.node_data.method == HttpRequestMethod.GET:
            response = request_method(
                self.node_data.url,
                headers=inputs_dict[HttpRequestInputType.HEADERS],
                params=inputs_dict[HttpRequestInputType.PARAMS],
            )
        else:
            # 5.其他請求方法需攜帶body參數
            response = request_method(
                self.node_data.url,
                headers=inputs_dict[HttpRequestInputType.HEADERS],
                params=inputs_dict[HttpRequestInputType.PARAMS],
                data=inputs_dict[HttpRequestInputType.BODY],
            )

        # 6.獲取響應文本和狀態碼
        text = response.text
        status_code = response.status_code

        # 7.提取並構建輸出數據結構
        outputs = {"text": text, "status_code": status_code}

        # 8.構建響應狀態並返回
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
