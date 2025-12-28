#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:37
@Author : zsting29@gmail.com
@File   : template_transform_entity.py
"""
from langchain_core.pydantic_v1 import Field, validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableValueType


class TemplateTransformNodeData(BaseNodeData):
    """模板轉換節點數據"""
    template: str = ""  # 需要拼接轉換的字串模板
    inputs: list[VariableEntity] = Field(default_factory=list)  # 輸入列表資訊
    outputs: list[VariableEntity] = Field(
        default_factory=lambda: [
            VariableEntity(
                name="output",
                value={"type": VariableValueType.GENERATED}
            )
        ]
    )

    @validator("outputs", pre=True)
    def validate_outputs(cls, outputs: list[VariableEntity]):
        return [
            VariableEntity(
                name="output",
                value={"type": VariableValueType.GENERATED}
            )
        ]
