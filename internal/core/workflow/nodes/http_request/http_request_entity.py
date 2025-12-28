#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:43
@Author : zsting29@gmail.com
@File   : http_request_entity.py
"""
from enum import Enum
from typing import Optional

from langchain_core.pydantic_v1 import Field, validator, HttpUrl

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableType, VariableValueType
from internal.exception import ValidateErrorException


class HttpRequestMethod(str, Enum):
    """Http請求方法類型枚舉"""
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"
    HEAD = "head"
    OPTIONS = "options"


class HttpRequestInputType(str, Enum):
    """Http請求輸入變數類型"""
    PARAMS = "params"  # query參數
    HEADERS = "headers"  # header請求頭
    BODY = "body"  # body參數


class HttpRequestNodeData(BaseNodeData):
    """HTTP請求節點數據"""
    url: Optional[HttpUrl] = None  # 請求URL地址
    method: HttpRequestMethod = HttpRequestMethod.GET  # API請求方法
    inputs: list[VariableEntity] = Field(default_factory=list)  # 輸入變數列表
    outputs: list[VariableEntity] = Field(
        default_factory=lambda: [
            VariableEntity(
                name="status_code",
                type=VariableType.INT,
                value={"type": VariableValueType.GENERATED, "content": 0},
            ),
            VariableEntity(name="text", value={"type": VariableValueType.GENERATED}),
        ],
    )

    @validator("url", pre=True, always=True)
    def validate_url(cls, url: Optional[HttpUrl]):
        return url if url != "" else None

    @validator("outputs", pre=True)
    def validate_outputs(cls, outputs: list[VariableEntity]):
        return [
            VariableEntity(
                name="status_code",
                type=VariableType.INT,
                value={"type": VariableValueType.GENERATED, "content": 0},
            ),
            VariableEntity(name="text", value={"type": VariableValueType.GENERATED}),
        ]

    @validator("inputs")
    def validate_inputs(cls, inputs: list[VariableEntity]):
        """校驗輸入列表數據"""
        # 1.校驗判斷輸入變數列表中的類型資訊
        for input in inputs:
            if input.meta.get("type") not in HttpRequestInputType.__members__.values():
                raise ValidateErrorException("Http請求參數結構出錯")

        # 2.返回校驗後的數據
        return inputs
