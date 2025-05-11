#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/11 下午1:30
@Author : zsting29@gmail.com
@File   : buildin_category_manager.py
"""
import os.path
from typing import Any

import yaml
from pydantic.v1 import BaseModel, Field

from internal.core.tools.buildin_tools.entities import CategoryEntity
from internal.exception import NotFoundException


class BuildinCategoryManager(BaseModel):
    """內置工具分類管理器"""
    category_map: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        """分類管理器初始化"""
        super().__init__(**kwargs)
        self._init_categories()

    def get_category_map(self) -> dict[str, Any]:
        """獲取分類映射訊息"""
        return self.category_map

    def _init_categories(self):
        """初始化分類數據"""
        # 1.檢測檢測數據是否已處理
        if self.category_map:
            return

        # 2.獲取數yaml據並加載
        current_path = os.path.abspath(__file__)
        category_path = os.path.dirname(current_path)
        category_yaml_path = os.path.join(category_path, "categories.yaml")
        with open(category_yaml_path, encoding="utf-8") as f:
            categories = yaml.safe_load(f)

        # 3.循環遍歷所有分類，並將分類加載成實體資訊
        for category in categories:
            # 4.創建分類實體資訊
            category＿entity = CategoryEntity(**category)

            # 5.獲取icon的位置並檢測icon是否存在
            icon_path = os.path.join(category_path, "icons", category＿entity.icon)
            if not os.path.exists(icon_path):
                raise NotFoundException(f"The category {category＿entity.category} icon is not available.")

            # 6.讀取對應的icon數據
            with open(icon_path, encoding="utf-8") as f:
                icon = f.read()

            # 7.將數據映射到字典
            self.category_map[category＿entity.category] = {
                "entity": category＿entity,
                "icon": icon
            }
