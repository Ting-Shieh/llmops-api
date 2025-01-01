#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/1 下午4:16
@Author : zsting29@gmail.com
@File   : response.py
"""
from dataclasses import field, dataclass
from typing import Any

from .http_code import HttpCode


@dataclass
class Response:
    """基礎HTTP接口響應格式"""
    code: HttpCode = HttpCode.SUCCESS
    message: str = ""
    data: Any = field(default_factory=dict)
