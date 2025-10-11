#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/1 下午2:36
@Author : zsting29@gmail.com
@File   : default_model_parameter_template.py
"""
from internal.core.language_model.entities.model_entity import (
    DefaultModelParameterName,
    ModelParameterType
)

# 默认模型参数模板，用于减少YAML的配置，参数以OpenAI的模型接口作为标准
DEFAULT_MODEL_PARAMETER_TEMPLATE = {
    # 溫度模板默認參數
    DefaultModelParameterName.TEMPERATURE: {
        "label": "溫度",
        "type": ModelParameterType.FLOAT,
        "help": "溫度控制隨機性，較低的溫度會導致較少的隨機生成。隨著溫度接近零，模型將變得更確定，較高的溫度會導致更多隨機內容被生成",
        "required": False,
        "default": 1,
        "min": 0,
        "max": 2,
        "precision": 2,
        "options": [],
    },
    # TopP核採樣
    DefaultModelParameterName.TOP_P: {
        "label": "Top P",
        "type": ModelParameterType.FLOAT,
        "help": "通過核心採樣控制多樣性，0.5表示考慮了一半的所有可能性加權選項",
        "required": False,
        "default": 0,
        "min": 0,
        "max": 1,
        "precision": 2,
        "options": [],
    },
    # 存在懲罰
    DefaultModelParameterName.PRESENCE_PENALTY: {
        "label": "存在懲罰",
        "type": ModelParameterType.FLOAT,
        "help": "對文本中已有的標記的對數機率施加懲罰。",
        "required": False,
        "default": 0,
        "min": -2.0,
        "max": 2.0,
        "precision": 2,
        "options": [],
    },
    # 頻率懲罰
    DefaultModelParameterName.FREQUENCY_PENALTY: {
        "label": "頻率懲罰",
        "type": ModelParameterType.FLOAT,
        "help": "對文本中已有的標記的對數機率施加懲罰。",
        "required": False,
        "default": 0,
        "min": -2.0,
        "max": 2.0,
        "precision": 2,
        "options": [],
    },
    # 最大生成tokens數
    DefaultModelParameterName.MAX_TOKENS: {
        "label": "最大標記",
        "type": ModelParameterType.INT,
        "help": "要生成的標記的最大數量，類型為整型",
        "required": False,
        "default": None,
        "min": 1,
        "max": 16384,
        "precision": 0,
        "options": [],
    },
}
