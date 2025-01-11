#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/11 下午2:04
@Author : zsting29@gmail.com
@File   : test_app_handler.py
"""
import pytest

from pkg.response import HttpCode


class TestAppHandler:
    """app 控制器的測試類"""

    @pytest.mark.parametrize("query", [None, "你好，你是？"])
    def test_completion(self, query, client):
        # resp = client.post("/app/completion", json={"query": "你好，你是？"})
        # resp = client.post("/app/completion", json={"query": None})
        # assert resp.status_code == 200
        # assert resp.json.get("code") == HttpCode.SUCCESS
        # assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        # print("響應內容：", resp.json)  # terminal >> pytest -s -v
        resp = client.post("/app/completion", json={"query": query})
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS
        print("響應內容：", resp.json)
