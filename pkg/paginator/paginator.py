#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/17 下午8:14
@Author : zsting29@gmail.com
@File   : paginator.py
"""
import math
from dataclasses import dataclass
from typing import Any

from flask_wtf import FlaskForm
from wtforms.fields.numeric import IntegerField
from wtforms.validators import Optional, NumberRange
from sqlalchemy import func

from pkg.sqlalchemy import SQLAlchemy


class PaginatorReq(FlaskForm):
    """分類請求基礎累，涵蓋當前頁數，每頁條數，如果接口請求需要攜帶分頁訊息，可直接繼承該類"""
    current_page = IntegerField(
        "current_page",
        default=1,
        validators=[
            Optional(),
            NumberRange(min=1, max=9999, message="當前頁數的範圍在1-9999")
        ]
    )

    page_size = IntegerField(
        "page_size",
        default=20,
        validators=[
            Optional(),
            NumberRange(min=1, max=50, message="每頁數據的條數範圍在1-50")
        ]
    )


@dataclass
class Paginator:
    """分頁器"""
    total_page: int = 0  # 總頁數
    total_record: int = 0  # 總條數
    current_page: int = 1  # 當前頁數
    page_size: int = 20.  # 每條數據

    def __init__(self, db: SQLAlchemy, req: PaginatorReq = None):
        if req is not None:
            self.current_page = req.current_page.data
            self.page_size = req.page_size.data
        self.db = db

    def paginate(self, query) -> list[Any]:
        """對傳入的查詢進行分頁"""
        try:
            # 1.調用db.paginate進行數據分頁
            p = self.db.paginate(query, page=self.current_page, per_page=self.page_size, error_out=False)

            # 2.計算總頁數+總條數
            self.total_record = p.total
            self.total_page = math.ceil(p.total / self.page_size)

            # 3.返回分頁後的數據
            return p.items
        except Exception as e:
            # 如果 paginate 方法失敗，使用手動分頁方式
            # 這是為了向後相容 SQLAlchemy 2.0+
            try:
                # 計算偏移量
                offset = (self.current_page - 1) * self.page_size
                
                # 獲取總數
                count_query = query.statement.with_only_columns([func.count()])
                self.total_record = self.db.session.execute(count_query).scalar()
                self.total_page = math.ceil(self.total_record / self.page_size)
                
                # 獲取分頁數據
                items = query.offset(offset).limit(self.page_size).all()
                return items
            except Exception as manual_error:
                # 如果手動分頁也失敗，返回空列表
                print(f"分頁查詢失敗: {manual_error}")
                self.total_record = 0
                self.total_page = 0
                return []


@dataclass
class PageModel:
    list: list[Any]
    paginator: Paginator
