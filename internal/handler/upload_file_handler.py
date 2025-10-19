#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/11 上午9:15
@Author : zsting29@gmail.com
@File   : upload_file_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.upload_file_schema import UploadFileReq, UploadFileResp, UploadImageReq
from internal.service import GcsService
from pkg.response import validate_error_json, success_json


@inject
@dataclass
class UploadFileHandler:
    """上傳文件處理器"""
    gcs_service: GcsService

    @login_required
    def upload_file(self):
        """上傳文件"""
        # 1.構建請求並校驗
        req = UploadFileReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 2.調用服務上傳文件並獲取紀錄
        upload_file = self.gcs_service.upload_file(req.file.data, False, current_user)

        # 3.構建響應並返回
        resp = UploadFileResp()
        return success_json(resp.dump(upload_file))

    @login_required
    def upload_image(self):
        """上傳圖片"""
        # 1.構建請求並校驗
        req = UploadImageReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務上傳文件並獲取紀錄
        upload_file = self.gcs_service.upload_file(req.file.datau, True, current_user)

        # 3.獲取圖片實際URL地址
        image_url = self.gcs_service.get_file_url(upload_file.key, signed=True, expiration_minutes=60)
        return success_json({"image_url": image_url})
