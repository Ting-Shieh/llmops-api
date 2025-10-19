#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/14 下午11:31
@Author : zsting29@gmail.com
@File   : app_service.py
"""
import uuid
from dataclasses import dataclass
from typing import Generator
from uuid import UUID

from injector import inject

from internal.entity.app_entity import DEFAULT_APP_CONFIG, AppStatus, AppConfigType
from internal.exception import ForbiddenException, NotFoundException
from internal.model import App, AppConfigVersion
from internal.model.account import Account
from internal.schema.app_schema import DebugChatReq, CreateAppReq
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class AppService(BaseService):
    """應用服務邏輯"""
    db: SQLAlchemy

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        """創建Agent應用服務"""
        # 1.開啟資料庫自動提交上下文
        with self.db.auto_commit():
            # 2.創建應用記錄，並刷新數據，從而可以拿到應用id
            app = App(
                account_id=account.id,
                name=req.name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 3.添加草稿記錄
            app_config_version = AppConfigVersion(
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 4.為應用添加草稿配置id
            app.draft_app_config_id = app_config_version.id

        # 5.返回創建的應用記錄
        return app

    def get_app(self, app_id: UUID, account: Account) -> App:
        """根據傳遞的id獲取應用的基礎資訊"""
        # 1.查詢資料庫獲取應用基礎資訊
        app = self.get(App, app_id)

        # 2.判斷應用是否存在
        if not app:
            raise NotFoundException("該應用不存在，請核實後重試")

        # 3.判斷當前帳號是否有權限訪問該應用
        if app.account_id != account.id:
            raise ForbiddenException("當前帳號無權限訪問該應用，請核實後嘗試")

        return app

    def update_app(self, app_id: UUID, account: Account, **kwargs) -> App:
        """根據傳遞的應用id+帳號+資訊，更新指定的應用"""
        app = self.get_app(app_id, account)
        self.update(app, **kwargs)
        return app

    def delete_app(self, app_id: UUID, account: Account) -> App:
        """根據傳遞的應用id+帳號，刪除指定的應用資訊，目前僅刪除應用基礎資訊即可"""
        app = self.get_app(app_id, account)
        self.delete(app)
        return app

    def debug_chat(
            self,
            app_id: uuid.UUID, req: DebugChatReq, account: Account
    ) -> Generator:
        pass
