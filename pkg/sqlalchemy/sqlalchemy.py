#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/16 下午9:59
@Author : zsting29@gmail.com
@File   : sqlalchemy.py
"""
from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy


class SQLAlchemy(_SQLAlchemy):
    """
    重寫flask_sqlalchemy中的核心類，
    實現自動提交
    """

    @contextmanager
    def auto_commit(self):
        try:
            yield
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
