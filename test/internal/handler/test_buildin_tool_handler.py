#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/11 下午3:57
@Author : zsting29@gmail.com
@File   : test_buildin_tool_handler.py
"""
from pkg.response import HttpCode


class TestBuildinToolHandler:
    def test_get_categpries(self, client):
        resp = client.get('/buildin-tool/categories')
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        assert len(resp.json.get("data")) > 0
