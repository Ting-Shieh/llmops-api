#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:45
@Author : zsting29@gmail.com
@File   : end_entity.py
"""
from langchain_core.pydantic_v1 import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class EndNodeData(BaseNodeData):
    """結束節點數據"""
    outputs: list[VariableEntity] = Field(default_factory=list)  # 結束節點需要輸出的數據
