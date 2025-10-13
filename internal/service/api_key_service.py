#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/12 下午1:39
@Author : zsting29@gmail.com
@File   : api_key_service.py
"""
import secrets
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.exception import ForbiddenException
from internal.model import Account, ApiKey
from internal.schema.api_key_schema import CreateApiKeyReq
from pkg.paginator import PaginatorReq, Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ApiKeyService(BaseService):
    """API秘鑰服務"""
    db: SQLAlchemy

    def create_api_key(self, req: CreateApiKeyReq, account: Account) -> ApiKey:
        """根據傳遞的資訊創建API秘鑰"""
        return self.create(
            ApiKey,
            account_id=account.id,
            api_key=self.generate_api_key(),
            is_active=req.is_active.data,
            remark=req.remark.data,
        )

    def get_api_key(self, api_key_id: UUID, account: Account) -> ApiKey:
        """根據傳遞的秘鑰id+帳號資訊獲取記錄"""
        api_key = self.get(ApiKey, api_key_id)
        if not api_key or api_key.account_id != account.id:
            raise ForbiddenException("API秘鑰不存在或無權限")
        return api_key

    def get_api_by_by_credential(self, api_key: str) -> ApiKey:
        """根據傳遞的憑證資訊獲取ApiKey記錄"""
        return self.db.session.query(ApiKey).filter(
            ApiKey.api_key == api_key,
        ).one_or_none()

    def update_api_key(self, api_key_id: UUID, account: Account, **kwargs) -> ApiKey:
        """根據傳遞的資訊更新API秘鑰"""
        api_key = self.get_api_key(api_key_id, account)
        self.update(api_key, **kwargs)
        return api_key

    def delete_api_key(self, api_key_id: UUID, account: Account) -> ApiKey:
        """根據傳遞的id刪除API秘鑰"""
        api_key = self.get_api_key(api_key_id, account)
        self.delete(api_key)
        return api_key

    def get_api_keys_with_page(self, req: PaginatorReq, account: Account) -> tuple[list[ApiKey], Paginator]:
        """根據傳遞的資訊獲取API秘鑰分頁列表數據"""
        # 1.構建分頁器
        paginator = Paginator(db=self.db, req=req)

        # 2.執行分頁並獲取數據
        api_keys = paginator.paginate(
            self.db.session.query(ApiKey).filter(
                ApiKey.account_id == account.id,
            ).order_by(desc("created_at"))
        )

        return api_keys, paginator

    @classmethod
    def generate_api_key(cls, api_key_prefix: str = "llmops-v1/") -> str:
        """生成一個長度為48的API秘鑰，並攜帶前綴"""
        return api_key_prefix + secrets.token_urlsafe(48)
