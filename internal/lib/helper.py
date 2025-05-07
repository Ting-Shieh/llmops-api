#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/6 下午9:32
@Author : zsting29@gmail.com
@File   : helper.py
"""
import importlib
from typing import Any


def dynamic_import(module_name: str, symbol_name: str) -> Any:
    """
    動態導入特定模塊下的特定功能
    :param module_name: 模塊名
    :param symbol_name: 模塊下的什麼數據
    :return:
    """

    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)
