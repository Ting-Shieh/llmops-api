#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:41
@Author : zsting29@gmail.com
@File   : tool_node.py
"""
import json
import time
from typing import Optional, Any

from langchain_core.pydantic_v1 import PrivateAttr
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

from internal.core.tools.api_tools.entities import ToolEntity
from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from internal.exception import FailException, NotFoundException
from internal.model import ApiTool
from .tool_entity import ToolNodeData


class ToolNode(BaseNode):
    """擴展插件節點"""
    node_data: ToolNodeData
    _tool: BaseTool = PrivateAttr(None)

    def __init__(self, *args: Any, **kwargs: Any):
        """構造函數，完成對內建工具的初始化"""
        # 1.調用父類構造函數完成數據初始化
        super().__init__(*args, **kwargs)

        # 2.導入依賴注入及工具提供者
        from app.http.module import injector

        # 3.判斷是內建插件還是API插件，執行不同的操作
        if self.node_data.tool_type == "builtin_tool":
            from internal.core.tools.buildin_tools.providers import BuiltinProviderManager
            builtin_provider_manager = injector.get(BuiltinProviderManager)

            # 4.調用內建提供者獲取內建插件
            _tool = builtin_provider_manager.get_tool(self.node_data.provider_id, self.node_data.tool_id)
            if not _tool:
                raise NotFoundException("該內建插件擴展不存在，請核實後重試")

            self._tool = _tool(**self.node_data.params)
        else:
            # 5.API插件，調用資料庫查詢記錄並創建API插件
            from pkg.sqlalchemy import SQLAlchemy
            db = injector.get(SQLAlchemy)

            # 6.根據傳遞的提供者名字+工具名字查詢工具
            api_tool = db.session.query(ApiTool).filter(
                ApiTool.provider_id == self.node_data.provider_id,
                ApiTool.name == self.node_data.tool_id
            ).one_or_none()
            if not api_tool:
                raise NotFoundException("該API擴展插件不存在，請核實重試")

            # 7.導入API插件提供者
            from internal.core.tools.api_tools.providers import ApiProviderManager
            api_provider_manager = injector.get(ApiProviderManager)

            # 8.創建API工具提供者並賦值
            self._tool = api_provider_manager.get_tool(ToolEntity(
                id=str(api_tool.id),
                name=api_tool.name,
                url=api_tool.url,
                method=api_tool.method,
                description=api_tool.description,
                headers=api_tool.provider.headers,
                parameters=api_tool.parameters,
            ))

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """擴展插件執行節點，根據傳遞的資訊調用預設的插件，涵蓋內建插件及API插件"""
        # 1.提取節點中的輸入數據
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 2.調用插件並獲取結果
        try:
            result = self._tool.invoke(inputs_dict)
        except Exception as e:
            raise FailException("擴展插件執行失敗，請稍後嘗試")

        # 3.檢測result是否為字串，如果不是則轉換
        if not isinstance(result, str):
            # 3.1[升級更新] 避免漢字被轉義
            result = json.dumps(result, ensure_ascii=False)

        # 4.提取並構建輸出數據結構
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = result
        else:
            outputs["text"] = result

        # 5.構建響應狀態並返回
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
