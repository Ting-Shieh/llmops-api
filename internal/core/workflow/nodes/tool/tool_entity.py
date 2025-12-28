#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:41
@Author : zsting29@gmail.com
@File   : tool_entity.py
"""
from typing import Any, Literal

from langchain_core.pydantic_v1 import Field, validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableValueType


class ToolNodeData(BaseNodeData):
    """工具節點數據"""
    tool_type: Literal["builtin_tool", "api_tool", ""] = Field(alias="type")  # 工具類型
    provider_id: str  # 工具提供者id
    tool_id: str  # 工具id
    params: dict[str, Any] = Field(default_factory=dict)  # 內建工具設置參數
    inputs: list[VariableEntity] = Field(default_factory=list)  # 輸入變數列表
    outputs: list[VariableEntity] = Field(
        default_factory=lambda: [
            VariableEntity(name="text", value={"type": VariableValueType.GENERATED})
        ]
    )  # 輸出欄位列表資訊

    @validator("outputs", pre=True)
    def validate_outputs(cls, outputs: list[VariableEntity]):
        return [
            VariableEntity(name="text", value={"type": VariableValueType.GENERATED})
        ]
