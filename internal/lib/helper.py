#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/6 下午9:32
@Author : zsting29@gmail.com
@File   : helper.py
"""
import importlib
from typing import Any

from markdown_it.common.html_re import attr_value


class ToolWrapper:
    """工具封裝類，使工具具有屬性並保持函數功能"""

    def __init__(self, func: Any, name: str):
        self.func = func
        self.name = name

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


def dynamic_import(module_name: str, symbol_name: str) -> Any:
    """
    動態導入特定模塊下的特定功能
    :param module_name: 模塊名
    :param symbol_name: 模塊下的什麼數據
    :return:
    """

    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)


def add_attribute(attr_name: str, att_value: Any):
    """
    裝飾器函數，為特定函數添加相應的屬性
    :param attr_name: 屬性名
    :param att_value: 屬性值
    :return:
    """

    def decorator(func):
        setattr(func, attr_name, attr_value)
        return func

    return decorator
