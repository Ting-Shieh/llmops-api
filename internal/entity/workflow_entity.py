#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/8 下午7:14
@Author : zsting29@gmail.com
@File   : workflow_entity.py
"""
from enum import Enum


class WorkflowStatus(str, Enum):
    """工作流狀態類型枚舉"""
    DRAFT = "draft"
    PUBLISHED = "published"


class WorkflowResultStatus(str, Enum):
    """工作流運行結果狀態"""
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


# 工作流默認配置資訊，默認添加一個空的工作流
DEFAULT_WORKFLOW_CONFIG = {
    "graph": {},
    "draft_graph": {
        "nodes": [],
        "edges": []
    },
}
