# !/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/20 上午7:27
@Author : zsting29@gmail.com
@File   : base_service.py
"""
from typing import Any, Optional

from internal.exception import FailException
from pkg.sqlalchemy import SQLAlchemy


class BaseService:
    """基礎服務,完善數據庫的基礎增刪改查部分，簡化代碼"""
    db: SQLAlchemy

    def create(self, model: Any, **kwargs) -> Any:
        """根據傳遞的模型類+鍵值對訊息創建數據庫紀錄"""
        with self.db.auto_commit():
            model_instance = model(**kwargs)
            self.db.session.add(model_instance)
        return model_instance

    def delete(self, model_instance: Any) -> Any:
        """根據傳遞的模型實例刪除數據庫紀錄"""
        with self.db.auto_commit():
            self.db.session.delete(model_instance)
        return model_instance

    def update(self, model_instance: Any, **kwargs) -> Any:
        """根據傳遞的模型類+鍵值對訊息更新數據庫紀錄"""
        with self.db.auto_commit():
            for field, value in kwargs.items():
                if hasattr(model_instance, field):
                    setattr(model_instance, field, value)
                else:
                    raise FailException("更新數據失敗．Updated data failed.")
        return model_instance

    def get(self, model: Any, primary_key: Any) -> Optional[Any]:
        """根據傳遞的模型類+主鍵獲取唯一訊息"""
        return self.db.session.query(model).get(primary_key)
