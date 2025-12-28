#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:35
@Author : zsting29@gmail.com
@File   : llm_entity.py
"""
from typing import Any

from langchain_core.pydantic_v1 import Field, validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableValueType
from internal.entity.app_entity import DEFAULT_APP_CONFIG


class LLMNodeData(BaseNodeData):
    """大語言模型節點數據"""
    prompt: str  # 大語言模型節點提示詞
    language_model_config: dict[str, Any] = Field(
        alias="model_config",
        default_factory=lambda: DEFAULT_APP_CONFIG["model_config"],
    )  # 大語言模型配置資訊
    inputs: list[VariableEntity] = Field(default_factory=list)  # 輸入列表資訊
    outputs: list[VariableEntity] = Field(
        default_factory=lambda: [
            VariableEntity(name="output", value={"type": VariableValueType.GENERATED})
        ]
    )

    @validator("outputs", pre=True)
    def validate_outputs(cls, value: list[VariableEntity]):
        return [
            VariableEntity(name="output", value={"type": VariableValueType.GENERATED})
        ]
