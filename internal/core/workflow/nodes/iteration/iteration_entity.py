#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:48
@Author : zsting29@gmail.com
@File   : iteration_entity.py
"""
from uuid import UUID

from langchain_core.pydantic_v1 import Field, validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableType, VariableValueType
from internal.exception import FailException


class IterationNodeData(BaseNodeData):
    """迭代節點數據"""
    workflow_ids: list[UUID]  # 需要迭代的工作流id
    inputs: list[VariableEntity] = Field(default_factory=lambda: [
        VariableEntity(
            name="inputs",
            type=VariableType.LIST_STRING,
            value={"type": VariableValueType.LITERAL, "content": []}
        )
    ])  # 輸入變數列表
    outputs: list[VariableEntity] = Field(default_factory=list)

    @validator("workflow_ids")
    def validate_workflow_ids(cls, value: list[UUID]):
        """校驗迭代的工作流數量是否小於等於1"""
        if len(value) > 1:
            raise FailException("迭代節點只能綁定一個工作流")
        return value

    @validator("inputs")
    def validate_inputs(cls, value: list[VariableEntity]):
        """校驗輸入變數是否正確"""
        # 1.判斷是否一個輸入變數，如果不是則拋出錯誤
        if len(value) != 1:
            raise FailException("迭代節點輸入變數資訊錯誤")

        # 2.判斷輸入變數類型及欄位是否出錯
        iteration_inputs = value[0]
        allow_types = [
            VariableType.LIST_STRING,
            VariableType.LIST_INT,
            VariableType.LIST_FLOAT,
            VariableType.LIST_BOOLEAN,
        ]
        if (
                iteration_inputs.name != "inputs"
                or iteration_inputs.type not in allow_types
                or iteration_inputs.required is False
        ):
            raise FailException("迭代節點輸入變數名字/類型/必填屬性出錯")

        return value

    @validator("outputs")
    def validate_outputs(cls, value: list[VariableEntity]):
        """固定節點的輸出為列表型字串，該節點會將工作流中的所有結果迭代儲存到該列表中"""
        return [
            VariableEntity(name="outputs", value={"type": VariableValueType.GENERATED})
        ]
