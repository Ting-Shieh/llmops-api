#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/11 上午9:27
@Author : zsting29@gmail.com
@File   : upload_file_schema.py
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileSize, FileAllowed
from marshmallow import Schema, fields, pre_dump

from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSION, ALLOWED_IMAGE_EXTENSION
from internal.model import UploadFile


class UploadFileReq(FlaskForm):
    """上傳文件請求"""
    file = FileField(
        "file",
        validators=[
            FileRequired("上傳文件不得為空"),
            FileSize(
                max_size=15 * 1024 * 1024,
                message="上傳文件大小不得超過15MB"
            ),
            FileAllowed(
                ALLOWED_DOCUMENT_EXTENSION,
                message=f"僅允許上傳${'/'.join(ALLOWED_DOCUMENT_EXTENSION)}"
            )
        ]
    )


class UploadFileResp(Schema):
    """上傳文件接口響應結構"""
    id = fields.UUID(dump_default="")
    account_id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    key = fields.String(dump_default="")
    url = fields.String(dump_default="")  # 新增：文件訪問 URL
    size = fields.Integer(dump_default=0)
    extension = fields.String(dump_default="")
    mime_type = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    # 映射數據
    @pre_dump
    def process_data(self, data: UploadFile, **kwargs):
        return {
            "id": data.id,
            "account_id": data.account_id,  # 修復：原本錯誤地返回 data.id
            "name": data.name,              # 修復
            "key": data.key,                # 修復
            "url": data.url,                # 新增：自動生成 URL
            "size": data.size,              # 修復
            "extension": data.extension,    # 修復
            "mime_type": data.mime_type,    # 修復
            "created_at": int(data.created_at.timestamp()),
        }


class UploadImageReq(FlaskForm):
    """上傳圖片請求"""
    file = FileField(
        "file",
        validators=[
            FileRequired("上傳圖片不得為空"),
            FileSize(
                max_size=15 * 1024 * 1024,
                message="上傳圖片大小不得超過15MB"
            ),
            FileAllowed(
                ALLOWED_IMAGE_EXTENSION,
                message=f"僅允許上傳${'/'.join(ALLOWED_IMAGE_EXTENSION)}"
            )
        ]
    )
