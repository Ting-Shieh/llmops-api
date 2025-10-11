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

from injector import inject

from internal.model import App
from internal.model.account import Account
from internal.schema.app_schema import DebugChatReq
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class AppService:
    """應用服務邏輯"""
    db: SQLAlchemy

    def create_app(self) -> App:
        with self.db.auto_commit():
            # 1.創建模型實體類
            app = App(
                name="Test Robot",
                account_id=uuid.uuid4(),
                icon="",
                description="這是測試機器人"
            )
            # 2.將實體類添加到session會話
            self.db.session.add(app)
        return app

    def get_app(self, id: uuid.UUID) -> App:
        app = self.db.session.query(App).get(id)
        return app

    def update_app(self, id: uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.get_app(id)
            app.name = "測試Robot"
        return app

    def delete_app(self, id: uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.get_app(id)
            self.db.session.delete(app)
        return app

    def debug_chat(
            self,
            app_id: uuid.UUID, req: DebugChatReq, account: Account
    ) -> Generator:
        pass
