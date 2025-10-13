#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/12 下午1:36
@Author : zsting29@gmail.com
@File   : password.py
"""
import base64
import binascii
import hashlib
import re
from typing import Any

# 密碼校驗正則，密碼最少包含一個字母、一個數字，並且長度在8-16
password_pattern = r"^(?=.*[a-zA-Z])(?=.*\d).{8,16}$"


def validate_password(password: str, pattern: str = password_pattern):
    """校驗傳入的密碼是否符合相應的匹配規則"""
    if re.match(pattern, password) is None:
        raise ValueError("密碼規則校驗失敗，至少包含一個字母，一個數字，並且長度為8-16位")
    return


def hash_password(password: str, salt: Any) -> bytes:
    """將傳入的密碼+顏值進行哈希加密"""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 10000)
    return binascii.hexlify(dk)


def compare_password(password: str, password_hashed_base64: Any, salt_base64: Any) -> bool:
    """根據傳遞的密碼+顏值校驗比對是否一致"""
    return hash_password(password, base64.b64decode(salt_base64)) == base64.b64decode(password_hashed_base64)
