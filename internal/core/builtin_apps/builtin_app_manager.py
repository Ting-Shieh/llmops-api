#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/2 上午12:18
@Author : zsting29@gmail.com
@File   : builtin_app_manager.py
"""
import os

import yaml
from injector import inject, singleton
from langchain_core.pydantic_v1 import BaseModel, Field

from internal.core.builtin_apps.entities.builtin_app_entity import BuiltinAppEntity
from internal.core.builtin_apps.entities.category_entity import CategoryEntity


@inject
@singleton
class BuiltinAppManager(BaseModel):
    """內建應用管理器"""
    builtin_app_map: dict[str, BuiltinAppEntity] = Field(default_factory=dict)
    categories: list[CategoryEntity] = Field(default_factory=list)

    def __init__(self, **kwargs):
        """構造函數，初始化對應的builtin_app_map"""
        super().__init__(**kwargs)
        self._init_categories()
        self._init_builtin_app_map()

    def get_builtin_app(self, builtin_app_id: str) -> BuiltinAppEntity:
        """根據傳遞的id獲取內建工具資訊"""
        return self.builtin_app_map.get(builtin_app_id, None)

    def get_builtin_apps(self) -> list[BuiltinAppEntity]:
        """獲取內建應用實體列表資訊"""
        return [builtin_app_entity for builtin_app_entity in self.builtin_app_map.values()]

    def get_categories(self) -> list[CategoryEntity]:
        """獲取內建應用實體分類列表資訊"""
        return self.categories

    def _init_builtin_app_map(self):
        """內建工具管理器初始化時初始化所有內建工具資訊"""
        # 1.檢測builtin_app_map是否為空
        if self.builtin_app_map:
            return

        # 2.獲取當前文件夾/類所在的文件夾路徑
        current_path = os.path.abspath(__file__)
        parent_path = os.path.dirname(current_path)
        builtin_apps_yaml_path = os.path.join(parent_path, "builtin_apps")

        # 3.循環遍歷builtin_apps_yaml_path讀取底下的所有yaml文件
        for filename in os.listdir(builtin_apps_yaml_path):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(builtin_apps_yaml_path, filename)

                # 4.讀取yaml數據
                with open(file_path, encoding="utf-8") as f:
                    builtin_app = yaml.safe_load(f)

                # 5.初始化內建應用數據並添加到字典中
                builtin_app["language_model_config"] = builtin_app.pop("model_config")
                self.builtin_app_map[builtin_app.get("id")] = BuiltinAppEntity(**builtin_app)

    def _init_categories(self):
        """初始化內建工具分類列表資訊"""
        # 1.檢測數據是否已經處理
        if self.categories:
            return

        # 2.獲取當前文件夾/類所在的文件夾路徑
        current_path = os.path.abspath(__file__)
        parent_path = os.path.dirname(current_path)
        categories_yaml_path = os.path.join(parent_path, "categories", "categories.yaml")

        # 3.讀取yaml數據
        with open(categories_yaml_path, encoding="utf-8") as f:
            categories = yaml.safe_load(f)

        # 4.循環遍歷所有分類數據並初始化
        for category in categories:
            self.categories.append(CategoryEntity(**category))
