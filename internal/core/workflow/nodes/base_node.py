#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:27
@Author : zsting29@gmail.com
@File   : base_node.py
"""
from abc import ABC

from langchain_core.runnables import RunnableSerializable

from internal.core.workflow.entities.node_entity import BaseNodeData


class BaseNode(RunnableSerializable, ABC):
    """工作流節點基類"""
    node_data: BaseNodeData
