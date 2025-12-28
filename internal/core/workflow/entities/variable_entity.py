#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:25
@Author : zsting29@gmail.com
@File   : variable_entity.py
"""
import re
from enum import Enum
from typing import Any, Optional, Union
from uuid import UUID

from langchain_core.pydantic_v1 import BaseModel, Field, validator

from internal.exception import ValidateErrorException


class VariableType(str, Enum):
    """變數的類型枚舉"""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    # 新增列表型數據
    LIST_STRING = "list[string]"
    LIST_INT = "list[int]"
    LIST_FLOAT = "list[float]"
    LIST_BOOLEAN = "list[BOOLEAN]"


# 變數類型與聲明的映射
VARIABLE_TYPE_MAP = {
    VariableType.STRING: str,
    VariableType.INT: int,
    VariableType.FLOAT: float,
    VariableType.BOOLEAN: bool,
    # 新增列表型數據類型映射
    VariableType.LIST_STRING: list[str],
    VariableType.LIST_INT: list[int],
    VariableType.LIST_FLOAT: list[float],
    VariableType.LIST_BOOLEAN: list[bool],
}

# 變數類型預設值映射
VARIABLE_TYPE_DEFAULT_VALUE_MAP = {
    VariableType.STRING: "",
    VariableType.INT: 0,
    VariableType.FLOAT: 0,
    VariableType.BOOLEAN: False,
    # 新增列表型數據預設值添加
    VariableType.LIST_STRING: [],
    VariableType.LIST_INT: [],
    VariableType.LIST_FLOAT: [],
    VariableType.LIST_BOOLEAN: [],
}

# 變數名字正則匹配規則
VARIABLE_NAME_PATTERN = r'^[A-Za-z_][A-Za-z0-9_-]*$'

# 描述最大長度
VARIABLE_DESCRIPTION_MAX_LENGTH = 1024


class VariableValueType(str, Enum):
    """變數內建值類型枚舉"""
    REF = "ref"  # 引用類型
    LITERAL = "literal"  # 字面數據/直接輸入
    GENERATED = "generated"  # 生成的值，一般用在開始節點或者output中


class VariableEntity(BaseModel):
    """變數實體資訊"""

    class Value(BaseModel):
        """變數的實體值資訊"""

        class Content(BaseModel):
            """變數內容實體資訊，如果類型為引用，則使用content記錄引用節點id+引用節點的變數名"""
            ref_node_id: Optional[UUID] = None
            ref_var_name: str = ""

            @validator("ref_node_id", pre=True, always=True)
            def validate_ref_node_id(cls, ref_node_id: Optional[UUID]):
                return ref_node_id if ref_node_id != "" else None

        type: VariableValueType = VariableValueType.LITERAL
        # 更新:基礎類型新增列表型數據，並允許為空，預設值為None
        content: Union[Content, str, int, float, bool, list[str], list[int], list[float], list[bool], None] = None

    name: str = ""  # 變數的名字
    description: str = ""  # 變數的描述資訊
    required: bool = True  # 變數是否必填
    type: VariableType = VariableType.STRING  # 變數的類型
    value: Value = Field(default_factory=lambda: {"type": VariableValueType.LITERAL, "content": ""})  # 變數對應的值
    meta: dict[str, Any] = Field(default_factory=dict)  # 變數元數據，儲存一些額外的資訊

    @validator("name")
    def validate_name(cls, value: str) -> str:
        """自訂校驗函數，用於校驗變數名字"""
        if not re.match(VARIABLE_NAME_PATTERN, value):
            raise ValidateErrorException("變數名字僅支持字母、數字和下劃線，且以字母/下劃線為開頭")
        return value

    @validator("description")
    def validate_description(cls, value: str) -> str:
        """自訂校驗函數，用於校驗描述資訊，截取前1024個字元"""
        return value[:VARIABLE_DESCRIPTION_MAX_LENGTH]
