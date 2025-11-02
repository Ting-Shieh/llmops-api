#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/6 下午9:32
@Author : zsting29@gmail.com
@File   : helper.py
"""
import importlib
import random
import string
from datetime import datetime
from enum import Enum
from hashlib import sha3_256
from typing import Any
from uuid import UUID

from langchain_core.documents import Document
from langchain_core.pydantic_v1 import BaseModel


# class ToolWrapper:
#     """工具封裝類，使工具具有屬性並保持函數功能"""
#
#     def __init__(self, func: Any, name: str):
#         self.func = func
#         self.name = name
#
#     def __call__(self, *args, **kwargs):
#         return self.func(*args, **kwargs)


def dynamic_import(module_name: str, symbol_name: str) -> Any:
    """
    動態導入特定模塊下的特定功能
    :param module_name: 模塊名
    :param symbol_name: 模塊下的什麼數據
    :return:
    """

    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)


def add_attribute(attr_name: str, attr_value: Any):
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


def generate_text_hash(text: str) -> str:
    """根據傳遞的文本計算對應的雜湊值"""
    # 1.將需要計算雜湊值的內容加上None這個字串，避免傳遞了空字串導致計算出錯
    text = str(text) + "None"

    # 2.使用sha3_256将数据转换成哈希值后返回
    return sha3_256(text.encode()).hexdigest()


def datetime_to_timestamp(dt: datetime) -> int:
    """將傳入的datetime時間轉換成時間戳，如果數據不存在則返回0"""
    if dt is None:
        return 0
    return int(dt.timestamp())


def combine_documents(documents: list[Document]) -> str:
    """將對應的文件列表使用換行符進行合併"""
    return "\n\n".join([document.page_content for document in documents])


def remove_fields(data_dict: dict, fields: list[str]) -> None:
    """根據傳遞的欄位名移除字典中指定的欄位"""
    for field in fields:
        data_dict.pop(field, None)


def convert_model_to_dict(obj: Any, *args, **kwargs):
    """輔助函數，將Pydantic V1版本中的UUID/Enum等數據轉換成可序列化儲存的數據。"""
    # 1.如果是Pydantic的BaseModel類型，遞迴處理其欄位
    if isinstance(obj, BaseModel):
        obj_dict = obj.dict(*args, **kwargs)
        # 2.遞迴處理嵌套欄位
        for key, value in obj_dict.items():
            obj_dict[key] = convert_model_to_dict(value, *args, **kwargs)
        return obj_dict

    # 3.如果是 UUID 類型，轉換為字串
    elif isinstance(obj, UUID):
        return str(obj)

    # 4.如果是 Enum 類型，轉換為其值
    elif isinstance(obj, Enum):
        return obj.value

    # 5.如果是列表類型，遞迴處理列表中的每個元素
    elif isinstance(obj, list):
        return [convert_model_to_dict(item, *args, **kwargs) for item in obj]

    # 6.如果是字典類型，遞迴處理字典中的每個欄位
    elif isinstance(obj, dict):
        return {key: convert_model_to_dict(value, *args, **kwargs) for key, value in obj.items()}

    # 7.對其他類型的欄位，保持原樣
    return obj


def get_value_type(value: Any) -> Any:
    """根據傳遞的值獲取變數的類型，並將str和bool轉換成string和boolean"""
    # 1.計算變數的類型並轉換成字串
    value_type = type(value).__name__

    # 2.判斷是否為str或者是bool
    if value_type == "str":
        return "string"
    elif value_type == "bool":
        return "boolean"

    return value_type


def generate_random_string(length: int = 16) -> str:
    """根據傳遞的位數，生成隨機字串"""
    # 1.定義字元集，包含大小寫字母和數字
    chars = string.ascii_letters + string.digits

    # 2.使用random.choices生成指定長度的隨機字串
    random_str = ''.join(random.choices(chars, k=length))

    return random_str
