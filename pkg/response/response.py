#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/1 下午4:16
@Author : zsting29@gmail.com
@File   : response.py
"""
from dataclasses import field, dataclass
from typing import Any

from flask import jsonify

from .http_code import HttpCode


@dataclass
class Response:
    """基礎HTTP接口響應格式"""
    code: HttpCode = HttpCode.SUCCESS
    message: str = ""
    data: Any = field(default_factory=dict)


def json(data: Response = None):
    """基礎響應接口"""
    return jsonify(data), 200


def success_json(data: Any = None):
    """成功數據響應"""
    return json(Response(
        code=HttpCode.SUCCESS,
        message="",
        data=data
    ))


def fail_json(data: Any = None):
    """失敗數據響應"""
    return json(Response(
        code=HttpCode.FAIL,
        message="",
        data=data
    ))


def validate_error_json(errors: dict = None):
    """數據驗證錯誤響應"""
    first_key = next(iter(errors))
    if first_key is not None:
        msg = errors.get(first_key)[0]
    else:
        msg = ""
    return json(Response(
        code=HttpCode.VALIDATE_ERROR,
        message=msg,
        data=errors
    ))


def message(code: HttpCode = None, msg: str = ""):
    """基礎消息響應，固定返回消息提示，數據固定為空字典"""
    return json(Response(
        code=code,
        message=msg,
        data={}
    ))


def success_message(msg: str = ""):
    """成功消息響應"""
    return message(code=HttpCode.SUCCESS, msg=msg)


def fail_message(msg: str = ""):
    """失敗消息響應"""
    return message(code=HttpCode.FAIL, msg=msg)


def not_found_message(msg: str = ""):
    """未找到消息響應"""
    return message(code=HttpCode.NOT_FOUND, msg=msg)


def unauthorized_message(msg: str = ""):
    """未授權消息響應"""
    return message(code=HttpCode.UNAUTHORIZED, msg=msg)


def forbidden_message(msg: str = ""):
    """無權限消息響應"""
    return message(code=HttpCode.FORBIDDEN, msg=msg)
