#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:22
@Author : zsting29@gmail.com
@File   : edge_entity.py
"""
from typing import Optional
from uuid import UUID

from langchain_core.pydantic_v1 import BaseModel

from internal.core.workflow.entities.node_entity import NodeType


class BaseEdgeData(BaseModel):
    """基礎邊數據"""
    id: UUID  # 邊記錄id
    source: UUID  # 邊起點對應的節點id
    source_type: NodeType  # 邊起點類型
    source_handle_id: Optional[UUID]  # 更新:添加起點句柄id，存在數據時則代表節點存在多個連接句柄
    target: UUID  # 邊目標對應的節點id
    target_type: NodeType  # 邊目標類型
