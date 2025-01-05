#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/1 下午4:08
@Author : zsting29@gmail.com
@File   : http_code.py
"""
from enum import Enum


class HttpCode(str, Enum):
    """HTTP基礎業務狀態碼"""
    SUCCESS = "success"  # 成功狀態
    FAIL = "fail"  # 失敗狀態
    NOT_FOUND = "not_found"  # 未找到
    UNAUTHORIZED = "unauthorized"  # 未授權
    FORBIDDEN = "borbidden"  # 無權限
    VALIDATE_ERROR = "validate_error"  # 數據驗證錯誤
