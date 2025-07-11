#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/19 上午6:48
@Author : zsting29@gmail.com
@File   : dataset_entity.py
"""
from enum import Enum

# 默認處理規則
# 默认知识库描述格式化文本
DEFAULT_DATASET_DESCRIPTION_FORMATTER = "當你需要回答管理《{name}》的時候可以引用該知識庫。"


class ProcessType(str, Enum):
    """文件處理規則類型枚舉"""
    AUTOMATIC = "automatic"
    CUSTOM = "custom"


# 預設的處理規則
DEFAULT_PROCESS_RULE = {
    "mode": "custom",
    "rule": {
        "pre_process_rules": [
            {"id": "remove_extra_space", "enabled": True},
            {"id": "remove_url_and_email", "enabled": True},
        ],
        "segment": {
            "separators": [
                "\n\n",
                "\n",
                "。|！|？",
                "\.\s|\!\s|\?\s",  # 英文標點符號後面通常需要加空格
                "；|;\s",
                "，|,\s",
                " ",
                ""
            ],
            "chunk_size": 500,
            "chunk_overlap": 50,
        }
    }
}


class DocumentStatus(str, Enum):
    """文件狀態類型枚舉"""
    WAITING = "waiting"
    PARSING = "parsing"
    SPLITTING = "splitting"
    INDEXING = "indexing"
    COMPLETED = "completed"
    ERROR = "error"


class SegmentStatus(str, Enum):
    """片段狀態類型枚舉"""
    WAITING = "waiting"
    INDEXING = "indexing"
    COMPLETED = "completed"
    ERROR = "error"


class RetrievalStrategy(str, Enum):
    """檢索策略類型枚舉"""
    FULL_TEXT = "full_text"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class RetrievalSource(str, Enum):
    """檢索來源"""
    HIT_TESTING = "hit_testing"
    APP = "app"
