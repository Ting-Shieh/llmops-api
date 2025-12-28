#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:29
@Author : zsting29@gmail.com
@File   : code_entity.py
"""
from langchain_core.pydantic_v1 import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity

# 預設的代碼
DEFAULT_CODE = """
def main(params):
    return params
"""


class CodeNodeData(BaseNodeData):
    """Python代碼執行節點數據"""
    code: str = DEFAULT_CODE  # 需要執行的Python代碼
    inputs: list[VariableEntity] = Field(default_factory=list)  # 輸入變數列表
    outputs: list[VariableEntity] = Field(default_factory=list)  # 輸出變數列表
