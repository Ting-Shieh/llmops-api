#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:32
@Author : zsting29@gmail.com
@File   : start_entity.py
"""
from langchain_core.pydantic_v1 import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class StartNodeData(BaseNodeData):
    """開始節點數據"""
    inputs: list[VariableEntity] = Field(default_factory=list)  # 開始節點的輸入變數資訊
