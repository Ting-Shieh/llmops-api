#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/1 上午10:06
@Author : zsting29@gmail.com
@File   : model_entity.py
"""
from abc import ABC
from enum import Enum
from typing import Any, Optional

from langchain_core.language_models import BaseLanguageModel as LCBaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.pydantic_v1 import BaseModel, Field


class DefaultModelParameterName(str, Enum):
    """預設的參數名字，一般是所有LLM都有的一些參數"""
    TEMPERATURE = "temperature"  # 溫度
    TOP_P = "top_p"  # 核採樣率
    PRESENCE_PENALTY = "presence_penalty"  # 存在懲罰
    FREQUENCY_PENALTY = "frequency_penalty"  # 頻率懲罰
    MAX_TOKENS = "max_tokens"  # 要生成的內容的最大tokens數


class ModelType(str, Enum):
    """模型類型枚舉"""
    CHAT = "chat"  # 聊天模型
    COMPLETION = "completion"  # 文本生成模型


class ModelParameterType(str, Enum):
    """模型參數類型"""
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"


class ModelParameterOption(BaseModel):
    """模型參數選項配置模型"""
    label: str  # 配置選項標籤
    value: Any  # 配置選項對應的值


class ModelParameter(BaseModel):
    """模型參數實體資訊"""
    name: str = ""  # 參數名字
    label: str = ""  # 參數標籤
    type: ModelParameterType = ModelParameterType.STRING  # 參數的類型
    help: str = ""  # 幫助資訊
    required: bool = False  # 是否必填
    default: Optional[Any] = None  # 默認參數值
    min: Optional[float] = None  # 最小值
    max: Optional[float] = None  # 最大值
    precision: int = 2  # 保留小數的位數
    options: list[ModelParameterOption] = Field(default_factory=list)  # 可選的參數配置


class ModelFeature(str, Enum):
    """模型特性，用於標記模型支持的特性資訊，涵蓋工具調用、智慧體推理、圖片輸入"""
    TOOL_CALL = "tool_call"  # 工具調用
    AGENT_THOUGHT = "agent_thought"  # 是否支持智慧體推理，一般要求參數量比較大，能回答通用型任務，如果不支持推理則會直接生成答案，而不進行中間步驟
    IMAGE_INPUT = "image_input"  # 圖片輸入，多模態大語言模型


class ModelEntity(BaseModel):
    """語言模型實體，記錄模型的相關資訊"""
    model_name: str = Field(default="", alias="model")  # 模型名字，使用model作為別名
    label: str = ""  # 模型標籤
    model_type: ModelType = ModelType.CHAT  # 模型類型
    features: list[ModelFeature] = Field(default_factory=list)  # 模型特徵資訊
    context_window: int = 0  # 上下文窗口長度(輸入+輸出的總長度)
    max_output_tokens: int = 0  # 最大輸出內容長度(輸出)
    attributes: dict[str, Any] = Field(default_factory=dict)  # 模型固定屬性字典
    parameters: list[ModelParameter] = Field(default_factory=list)  # 模型參數欄位規則列表，用於記錄模型的配置參數
    metadata: dict[str, Any] = Field(default_factory=dict)  # 模型元數據，用於儲存模型的額外數據，例如價格、詞表等等資訊


class BaseLanguageModel(LCBaseLanguageModel, ABC):
    """基礎語言模型"""
    features: list[ModelFeature] = Field(default_factory=list)  # 模型特性
    metadata: dict[str, Any] = Field(default_factory=dict)  # 模型元數據資訊

    def get_pricing(self) -> tuple[float, float, float]:
        """獲取LLM對應的價格資訊，返回數據格式為(輸入價格, 輸出價格, 單位)"""
        # 1.計算獲取輸入價格、輸出價格、單位
        input_price = self.metadata.get("pricing", {}).get("input", 0.0)
        output_price = self.metadata.get("pricing", {}).get("output", 0.0)
        unit = self.metadata.get("pricing", {}).get("unit", 0.0)

        # 2.返回數據
        return input_price, output_price, unit

    def convert_to_human_message(self, query: str, image_urls: list[str] = None) -> HumanMessage:
        """將傳遞的query+image_url轉換成人類消息HumanMessage，如果沒有傳遞image_url或者該LLM不支持image_input，則直接返回普通人類消息"""
        # 1.判斷圖片url是否為空，或者該LLM不支持圖片輸入，則直接返回普通消息
        if image_urls is None or len(image_urls) == 0 or ModelFeature.IMAGE_INPUT not in self.features:
            return HumanMessage(content=query)

        # 2.存在圖片輸入並且支持多模態輸入，則按照OpenAI規則轉換成人類消息，如果模型有差異則直接繼承重寫
        #   連結: https://python.langchain.com/docs/how_to/multimodal_inputs/
        return HumanMessage(content=[
            {"type": "text", "text": query},
            *[{"type": "image_url", "image_url": {"url": image_url}} for image_url in image_urls],
        ])
