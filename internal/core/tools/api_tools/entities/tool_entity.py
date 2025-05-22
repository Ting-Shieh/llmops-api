#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/21 下午10:57
@Author : zsting29@gmail.com
@File   : tool_entity.py
"""
from pydantic import BaseModel, Field


class ToolEntity(BaseModel):
    """API工具實體訊息，記錄了創建LangChain工具所需要配置訊息"""
    id: str = Field(default="", description="API提供者對應的ID")
    name: str = Field(default="", description="API工具的名稱")
    url: str = Field(default="", description="API工具發起請求的URL地址")
    method: str = Field(default="", description="API工具發起請求的方法")
    description: str = Field(default="", description="API工具的描述訊息")
    headers: list[dict] = Field(default_factory=list, description="API工具的請求頭訊息")
    parameters: list[dict] = Field(default_factory=list, description="API工具的請參數列表訊息")
