#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/1 下午5:37
@Author : zsting29@gmail.com
@File   : exception.py
"""
from dataclasses import field
from typing import Any

from pkg.response import HttpCode


class CustomException(Exception):
    """基礎自定義異常訊息"""
    code: HttpCode = HttpCode.FAIL
    message: str = ""
    data: Any = field(default_factory=dict)

    def __init__(self, message: str = None, data: Any = None):
        super().__init__()
        self.message = message
        self.data = data


class FailException(CustomException):
    """通用失敗異常"""
    pass


class NotFoundException(CustomException):
    """未找到數據異常"""
    code = HttpCode.NOT_FOUND


class UnauthorizedException(CustomException):
    """未授權異常"""
    code = HttpCode.UNAUTHORIZED


class ForbiddenException(CustomException):
    """無權限異常"""
    code = HttpCode.FORBIDDEN


class ValidateErrorException(CustomException):
    """數據驗證異常"""
    code = HttpCode.VALIDATE_ERROR
