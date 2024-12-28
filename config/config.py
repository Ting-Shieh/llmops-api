#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/28 下午5:41
@Author : zsting29@gmail.com
@File   : config.py
"""


class Config:
    def __init__(self):
        # 關閉 wtf 的 csrf 保護
        self.WTF_CSRF_ENABLED = False
