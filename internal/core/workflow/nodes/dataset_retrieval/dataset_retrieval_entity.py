#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:38
@Author : zsting29@gmail.com
@File   : dataset_retrieval_entity.py
"""
from uuid import UUID

from langchain_core.pydantic_v1 import BaseModel, Field, validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableType, VariableValueType
from internal.entity.dataset_entity import RetrievalStrategy
from internal.exception import FailException


class RetrievalConfig(BaseModel):
    """檢索配置"""
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC  # 檢索策略
    k: int = 4  # 最大召回數量
    score: float = 0  # 得分閾值


class DatasetRetrievalNodeData(BaseNodeData):
    """知識庫檢索節點數據"""
    dataset_ids: list[UUID]  # 關聯的知識庫id列表
    retrieval_config: RetrievalConfig = RetrievalConfig()  # 檢索配置
    inputs: list[VariableEntity] = Field(default_factory=list)  # 輸入變數資訊
    outputs: list[VariableEntity] = Field(
        default_factory=lambda: [
            VariableEntity(
                name="combine_documents",
                value={"type": VariableValueType.GENERATED}
            )
        ]
    )

    @validator("outputs", pre=True)
    def validate_outputs(cls, value: list[VariableEntity]):
        return [
            VariableEntity(
                name="combine_documents",
                value={"type": VariableValueType.GENERATED}
            )
        ]

    @validator("inputs")
    def validate_inputs(cls, value: list[VariableEntity]):
        """校驗輸入變數資訊"""
        # 1.判斷是否只有一個輸入變數，如果有多個則拋出錯誤
        if len(value) != 1:
            raise FailException("知識庫節點輸入變數資訊出錯")

        # 3.判斷輸入遍歷那個的類型及欄位名稱是否出錯
        query_input = value[0]
        if query_input.name != "query" or query_input.type != VariableType.STRING or query_input.required is False:
            raise FailException("知識庫節點輸入變數名字/變數類型/必填屬性出錯")

        return value
