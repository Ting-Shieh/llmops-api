#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/11 下午2:09
@Author : zsting29@gmail.com
@File   : upload_file_service.py
"""
from dataclasses import dataclass

from injector import inject

from internal.model import UploadFile
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class UploadFileService(BaseService):
    """上傳文件紀錄服務"""
    db: SQLAlchemy

    def create_upload_file(self, **kwargs) -> UploadFile:
        return self.create(UploadFile, **kwargs)
