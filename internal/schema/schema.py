#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/16 上午12:00
@Author : zsting29@gmail.com
@File   : schema.py
"""
from wtforms.fields.core import Field


class ListField(Field):
    """自定義list字段，用於存儲列表行數據"""
    data: list = None

    def process_formdata(self, valuelist):
        """"""
        if valuelist is not None and isinstance(valuelist, list):
            self.data = valuelist

    def _value(self):
        return self.data if self.data else []
