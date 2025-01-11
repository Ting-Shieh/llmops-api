#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/11 下午2:20
@Author : zsting29@gmail.com
@File   : conftest.py
"""
import pytest

from app.http.app import app


@pytest.fixture
def client():
    """獲取Flask應用的測試應用，並返回"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
