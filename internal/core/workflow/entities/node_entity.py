#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:23
@Author : zsting29@gmail.com
@File   : node_entity.py
"""
from enum import Enum
from typing import Any
from uuid import UUID

from langchain_core.pydantic_v1 import BaseModel, Field


class NodeType(str, Enum):
    """節點類型枚舉"""
    START = "start"
    LLM = "llm"
    TOOL = "tool"
    CODE = "code"
    DATASET_RETRIEVAL = "dataset_retrieval"
    HTTP_REQUEST = "http_request"
    TEMPLATE_TRANSFORM = "template_transform"
    # 新增意圖識別分類節點
    QUESTION_CLASSIFIER = "question_classifier"
    # 新增迭代節點
    ITERATION = "iteration"
    END = "end"


class BaseNodeData(BaseModel):
    """基礎節點數據"""

    class Position(BaseModel):
        """節點坐標基礎模型"""
        x: float = 0
        y: float = 0

    class Config:
        allow_population_by_field_name = True  # 允許通過欄位名進行賦值

    id: UUID  # 節點id，數值必須唯一
    node_type: NodeType  # 節點類型
    title: str = ""  # 節點標題，數據也必須唯一
    description: str = ""  # 節點描述資訊
    position: Position = Field(default_factory=lambda: {"x": 0, "y": 0})  # 節點對應的坐標資訊


class NodeStatus(str, Enum):
    """節點狀態"""
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class NodeResult(BaseModel):
    """節點運行結果"""
    node_data: BaseNodeData  # 節點基礎數據
    status: NodeStatus = NodeStatus.RUNNING  # 節點運行狀態
    inputs: dict[str, Any] = Field(default_factory=dict)  # 節點的輸入數據
    outputs: dict[str, Any] = Field(default_factory=dict)  # 節點的輸出數據
    latency: float = 0  # 節點響應耗時
    error: str = ""  # 節點運行錯誤資訊
