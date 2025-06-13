#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/11 上午11:23
@Author : zsting29@gmail.com
@File   : gcs_client.py
"""
# internal/service/gcs_client.py

import os
from datetime import timedelta

from dotenv import load_dotenv
from google.cloud import storage


class GCSClient:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dotenv_path = os.path.join(BASE_DIR, ".env")
        load_dotenv(dotenv_path)

        service_account_path = os.getenv("GCS_KEY_PATH")
        if not service_account_path:
            raise ValueError("環境變數 GCS_KEY_PATH 未設定！")

        service_account_full_path = os.path.join(BASE_DIR, service_account_path)
        self.client = storage.Client.from_service_account_json(service_account_full_path)

        # 預設 bucket name（建議你在 .env 加 GCS_BUCKET_NAME）
        self.default_bucket = os.getenv("GCS_BUCKET_NAME")
        if not self.default_bucket:
            raise ValueError("環境變數 GCS_BUCKET_NAME 未設定！")

    def get_bucket(self, bucket_name: str = None):
        bucket = self.client.bucket(bucket_name or self.default_bucket)
        return bucket

    def upload_file(self, file_bytes: bytes, destination_blob_name: str, bucket_name: str = None):
        bucket = self.get_bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes)
        print(f"已上傳檔案到 GCS {destination_blob_name}")

    def download_file(self, blob_name: str, destination_path: str, bucket_name: str = None):
        bucket = self.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(destination_path)
        print(f"已下載 {blob_name} 到 {destination_path}")

    def list_files(self, prefix: str = "", bucket_name: str = None):
        bucket = self.client.bucket(bucket_name or self.default_bucket)
        blobs = bucket.list_blobs(prefix=prefix)
        files = [blob.name for blob in blobs]
        print(f"列出檔案 prefix='{prefix}': {files}")
        return files

    def file_exists(self, blob_name: str, bucket_name: str = None) -> bool:
        bucket = self.client.bucket(bucket_name or self.default_bucket)
        blob = bucket.blob(blob_name)
        exists = blob.exists()
        print(f"檔案 {blob_name} 存在: {exists}")
        return exists

    def delete_file(self, blob_name: str, bucket_name: str = None):
        bucket = self.client.bucket(bucket_name or self.default_bucket)
        blob = bucket.blob(blob_name)
        blob.delete()
        print(f"已刪除檔案 {blob_name}")

    def generate_signed_url(self, blob_name: str, expiration_minutes: int = 60, bucket_name: str = None) -> str:
        bucket = self.client.bucket(bucket_name or self.default_bucket)
        blob = bucket.blob(blob_name)
        url = blob.generate_signed_url(expiration=timedelta(minutes=expiration_minutes))
        print(f"產生 signed url: {url}")
        return url


# 建立全域 gcs_client 供 service 層使用
gcs_client = GCSClient()
