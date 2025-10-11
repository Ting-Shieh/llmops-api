#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/29 下午1:35
@Author : zsting29@gmail.com
@File   : app_entity.py
"""
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
