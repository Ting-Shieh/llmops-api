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
            "frequency_penalty": 0.2,  # 頻率懲罰
            "presence_penalty": 0.2,  # 存在懲罰
            "max_tokens": 8192,  # 大語言模型可出的最大數
        },
    },
    "dialog_round": 3,  # 協帶參考上下文輪數
    "preset_prompt": "",  # 預設prompt => 默認沒有設置任何的人設以回覆邏輯
    "tools": [],  # 工具列表
    "workflows": [],  # 工作流列表
    "datasets": [],  # 知識庫列表
    # 檢索配置
    "retrieval_config": {
        "retrieval_strategy": "semantic",  # 檢索策略默認,使用相似性搜索
        "k": 10,  #
        "score": 0.5,  # 得分
    },
    # 長期記憶
    "long_term_memory": {
        "enable": False,
    },
    "opening_statement": "",  # 對話開場白
    "opening_questions": [],  # 對話開場白建議問題
    # 語音配置
    "speech_to_text": {  # 語音轉文本
        "enable": False,
    },
    "text_to_speech": {  # 文本轉語音
        "enable": False,
        "voice": "echo",  #
        "auto_play": False,  #
    },
    "suggested_after_answer": {
        "enable": True,
    },
    "review_config": {
        "enable": False,
        "keywords": [],
        # 輸入配置
        "inputs_config": {
            "enable": False,
            "preset_response": "",
        },
        # 輸出配置
        "outputs_config": {
            "enable": False,
        },
    },
}
