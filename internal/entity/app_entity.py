#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/29 下午1:35
@Author : zsting29@gmail.com
@File   : app_entity.py
"""
from enum import Enum

# 生成icon描述提示詞模板
GENERATE_ICON_PROMPT_TEMPLATE = """你是一個擁有10年經驗的AI繪畫工程師，可以將用戶傳遞的`應用名稱`和`應用描述`轉換為對應應用的icon描述。
該描述主要用於DallE AI繪畫，並且該描述是英文，用戶傳遞的數據如下:

應用名稱: {name}。
應用描述: {description}。

並且除了icon描述提示詞外，其他什麼都不要生成"""


class AppStatus(str, Enum):
    """應用狀態枚舉類"""
    DRAFT = "draft"
    PUBLISHED = "published"


class AppConfigType(str, Enum):
    """應用配置類型枚舉類"""
    DRAFT = "draft"
    PUBLISHED = "published"


# 應用默認配置資訊
DEFAULT_APP_CONFIG = {
    "model_config": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "parameters": {
            "temperature": 0.5,
            "top_p": 0.85,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.2,
            "max_tokens": 8192,
        },
    },
    "dialog_round": 3,
    "preset_prompt": "",
    "tools": [],
    "workflows": [],
    "datasets": [],
    "retrieval_config": {
        "retrieval_strategy": "semantic",
        "k": 10,
        "score": 0.5,
    },
    "long_term_memory": {
        "enable": False,
    },
    "opening_statement": "",
    "opening_questions": [],
    "speech_to_text": {
        "enable": False,
    },
    "text_to_speech": {
        "enable": False,
        "voice": "echo",
        "auto_play": False,
    },
    "suggested_after_answer": {
        "enable": True,
    },
    "review_config": {
        "enable": False,
        "keywords": [],
        "inputs_config": {
            "enable": False,
            "preset_response": "",
        },
        "outputs_config": {
            "enable": False,
        },
    },
}
