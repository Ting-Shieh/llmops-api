#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/2 下午10:01
@Author : zsting29@gmail.com
@File   : builtin_app_service.py
"""
from dataclasses import dataclass

from injector import inject

from internal.core.builtin_apps import BuiltinAppManager
from internal.core.builtin_apps.entities.builtin_app_entity import BuiltinAppEntity
from internal.core.builtin_apps.entities.category_entity import CategoryEntity
from internal.entity.app_entity import AppConfigType
from internal.entity.app_entity import AppStatus
from internal.exception import NotFoundException
from internal.model import Account, App, AppConfigVersion
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class BuiltinAppService(BaseService):
    """內建應用服務"""
    db: SQLAlchemy
    builtin_app_manager: BuiltinAppManager

    def get_categories(self) -> list[CategoryEntity]:
        """獲取分類列表資訊"""
        return self.builtin_app_manager.get_categories()

    def get_builtin_apps(self) -> list[BuiltinAppEntity]:
        """獲取所有內建應用實體資訊列表"""
        return self.builtin_app_manager.get_builtin_apps()

    def add_builtin_app_to_space(self, builtin_app_id: str, account: Account) -> App:
        """將指定的內建應用添加到個人空間下"""
        # 1.獲取內建應用資訊，並檢測是否存在
        builtin_app = self.builtin_app_manager.get_builtin_app(builtin_app_id)
        if not builtin_app:
            raise NotFoundException("該內建應用不存在，請核實後重試")

        # 2.創建自定提交上下文
        with self.db.auto_commit():
            # 3.創建應用資訊
            app = App(
                account_id=account.id,
                status=AppStatus.DRAFT,
                **builtin_app.dict(include={"name", "icon", "description"})
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 4.創建草稿配置資訊
            draft_app_config = AppConfigVersion(
                app_id=app.id,
                model_config=builtin_app.language_model_config,
                config_type=AppConfigType.DRAFT,
                **builtin_app.dict(include={
                    "dialog_round", "preset_prompt", "tools", "retrieval_config", "long_term_memory",
                    "opening_statement", "opening_questions", "speech_to_text", "text_to_speech",
                    "review_config", "suggested_after_answer",
                })
            )
            self.db.session.add(draft_app_config)
            self.db.session.flush()

            # 5.更新應用草稿配置
            app.draft_app_config_id = draft_app_config.id

        return app
