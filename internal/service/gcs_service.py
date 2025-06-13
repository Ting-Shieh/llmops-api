#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/11 上午10:48
@Author : zsting29@gmail.com
@File   : gcs_service.py
"""
import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import datetime

from injector import inject
from werkzeug.datastructures import FileStorage

from config.gcs_client import gcs_client
from internal.entity.upload_file_entity import ALLOWED_IMAGE_EXTENSION, ALLOWED_DOCUMENT_EXTENSION
from internal.exception import FailException
from internal.model import UploadFile
from internal.service.upload_file_service import UploadFileService


@inject
@dataclass
class GcsService:
    """GCS對象存儲服務"""
    upload_file_service: UploadFileService

    def upload_file(self, file: FileStorage, only_image: bool = False) -> UploadFile:
        """上傳文件到GCS對象存儲服務，並返回詳細資料"""
        # todo: 等待授權認證模塊完成進行切換調整
        account_id = "f2ac22f0-e5c6-be86-87c1-9e55c419aa2d"

        # . 1.提取文件拓展名，並檢測是否可以上傳
        filename = file.filename
        extension = filename.rsplit('.', 1)[-1] if '.' in filename else ""
        if extension.lower() not in (ALLOWED_IMAGE_EXTENSION + ALLOWED_DOCUMENT_EXTENSION):
            raise FailException(f"該.{extension}拓展文件格式，不允許上傳．")
        elif only_image and extension not in ALLOWED_IMAGE_EXTENSION:
            raise FailException(f"該.{extension}拓展文件格式，不允許上傳，請上傳正確的圖片")

        # 2.獲取客戶端＆bucket
        client = self._get_client()

        # 3.生成一個隨機名
        random_filename = str(uuid.uuid4()) + '.' + extension
        now = datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"

        # 4. 流式讀取上傳數據
        file_content = file.stream.read()

        # 5. 上傳到 GCS
        try:
            client.upload_file(file_bytes=file_content, destination_blob_name=upload_filename)
        except Exception as e:
            raise FailException("上傳文件失敗，請稍後重試")

        # 6. 建立 UploadFile record
        return self.upload_file_service.create_upload_file(
            account_id=account_id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash=hashlib.sha3_256(file_content).hexdigest(),
        )

    def download_file(self, key: str, target_file_path: str):
        """下載 GCS 的文件到本地的指定路徑"""
        client = self._get_client()  # GCSClient
        client.download_file(blob_name=key, destination_path=target_file_path)

    @classmethod
    def get_file_url(
            cls,
            key: str,
            signed: bool = True,
            expiration_minutes: int = 60
    ) -> str:
        """獲取 GCS 的雲端實際的圖片URL地址"""
        if signed:
            client = cls._get_client()
            return client.generate_signed_url(blob_name=key, expiration_minutes=expiration_minutes)
        else:
            bucket = os.getenv("GCS_BUCKET_NAME")
            return f"https://storage.googleapis.com/{bucket}/{key}"

    @classmethod
    def _get_client(cls):
        """獲取GCS對象存客戶端"""
        return gcs_client

    @classmethod
    def _get_bucket(cls):
        """獲取儲存桶"""
        client = cls._get_client()
        bucket = client.get_bucket()  # 使用 GCSClient 裡 get_bucket()
        return bucket
