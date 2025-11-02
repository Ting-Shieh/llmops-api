#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/15 下午11:24
@Author : zsting29@gmail.com
@File   : queue_entity.py
"""
from enum import Enum
from uuid import UUID

from pydantic.v1 import Field, BaseModel

from internal.entity.conversation_entity import MessageStatus


class QueueEvent(str, Enum):
    """隊列事件枚舉類型"""
    LONG_TERM_MEMORY_RECALL = "long_term_memory_recall"  # 長期記憶召回事件
    AGENT_THOUGHT = "agent_thought"  # 智慧體觀察事件
    AGENT_MESSAGE = "agent_message"  # 智慧體消息事件
    AGENT_ACTION = "agent_action"  # 智慧體動作
    DATASET_RETRIEVAL = "dataset_retrieval"  # 知識庫檢索事件
    AGENT_END = "agent_end"  # 智慧體結束事件
    STOP = "stop"  # 智慧體停止事件
    ERROR = "error"  # 智慧體錯誤事件
    TIMEOUT = "timeout"  # 智慧體超時事件
    PING = "ping"  # ping聯通事件


class AgentThought(BaseModel):
    """智慧體推理觀察輸出內容"""
    id: UUID  # 事件對應的id，同一個事件的id是一樣的
    task_id: UUID  # 任務id

    # 事件的推理與觀察
    event: QueueEvent
    thought: str = ""  # LLM推理內容
    observation: str = ""  # 觀察內容

    # 工具相關的欄位
    tool: str = ""  # 調用工具的名字
    tool_input: dict = Field(default_factory=dict)  # 工具的輸入

    # 消息相關的數據
    message: list[dict] = Field(default_factory=dict)  # 推理使用的消息列表
    message_token_count: int = 0  # 消息花費的token數
    message_unit_price: float = 0  # 單價
    message_price_unit: float = 0  # 價格單位

    # 答案相關的數據
    answer: str = ""  # LLM生成的最終答案
    answer_token_count: int = 0  # LLM生成答案的token數
    answer_unit_price: float = 0  # 單價
    answer_price_unit: float = 0  # 價格單位

    # Agent推理統計相關
    total_token_count: int = 0  # 總token消耗數量
    total_price: float = 0  # 總價格
    latency: float = 0  # 步驟推理耗時


class AgentResult(BaseModel):
    """智慧體推理觀察最終結果(開放API模塊)"""
    query: str = ""  # 原始用戶提問
    image_urls: list[str] = Field(default_factory=list)  # 用戶的圖片輸入列表

    message: list[dict] = Field(default_factory=list)  # 產生最終答案的消息列表
    message_token_count: int = 0  # 消息花費的token數
    message_unit_price: float = 0  # 單價
    message_price_unit: float = 0  # 價格單位

    answer: str = ""  # Agent產生的最終答案
    answer_token_count: int = 0  # LLM生成答案的token數
    answer_unit_price: float = 0  # 單價
    answer_price_unit: float = 0  # 價格單位

    total_token_count: int = 0  # 總token消耗數量
    total_price: float = 0  # 總價格
    latency: float = 0  # 總耗時

    status: str = MessageStatus.NORMAL  # 消息的狀態
    error: str = ""  # 錯誤資訊

    agent_thoughts: list[AgentThought] = Field(default_factory=list)  # 產生答案的推理步驟
