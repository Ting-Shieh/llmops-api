#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/7 下午10:14
@Author : zsting29@gmail.com
@File   : current_time.py
"""
from datetime import datetime
from typing import Any

from langchain_core.tools import BaseTool


class CurrentTimeTool(BaseTool):
    """一個用於獲取當前時間的工具"""
    name = "current_time"
    description = "一個用於獲取當前時間的工具"

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """獲取系統當前時間，並進行格式化後返回"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")


def current_time(**kwargs) -> BaseTool:
    """返回獲取當前時間的LangChain工具"""
    return CurrentTimeTool()
