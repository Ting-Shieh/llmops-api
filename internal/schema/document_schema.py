#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/5 上午8:18
@Author : zsting29@gmail.com
@File   : document_schema.py
"""
import uuid

from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, AnyOf, ValidationError

from internal.entity.dataset_entity import ProcessType, DEFAULT_PROCESS_RULE
from internal.model import Document
from internal.schema import ListField
from internal.schema.schema import DictField
from pkg.paginator import PaginatorReq


class CreateDocumentsReq(FlaskForm):
    """創建/新增文件列表請求"""
    upload_file_ids = ListField("upload_file_ids")
    process_type = StringField("process_type", validators=[
        DataRequired("文件處理類型不能為空"),
        AnyOf(values=[ProcessType.AUTOMATIC, ProcessType.CUSTOM], message="处理类型格式错误")
    ])
    rule = DictField("rule")

    def validate_upload_file_ids(self, field: ListField) -> None:
        """校驗上傳文件id列表"""
        # 1.校驗數據類型與非空
        if not isinstance(field.data, list):
            raise ValidationError("文件id列表格式必須是數組")

        # 2.校驗數據的長度，最長不能超過10條紀錄
        if len(field.data) == 0 or len(field.data) > 10:
            raise ValidationError("新增的文件數範圍在0-10")

        # 3.循環校驗id是否為uuid
        for upload_file_id in field.data:
            try:
                uuid.UUID(upload_file_id)
            except Exception as e:
                raise ValidationError("文件id的格式必須是UUID")

        # 4.刪除重複數據並更新
        field.data = list(dict.fromkeys(field.data))

    def validate_rule(self, field: DictField) -> None:
        """校驗上傳處理規則"""
        # 1.校驗處理模式，如果為自動，則為rule賦值預設值
        if self.process_type.data == ProcessType.AUTOMATIC:
            field.data = DEFAULT_PROCESS_RULE["rule"]
        else:
            # 2.檢測自訂處理類型下是否傳遞了rule
            if not isinstance(field.data, dict) or len(field.data) == 0:
                raise ValidationError("自訂處理模式下，rule不能為空")

            # 3.校驗pre_process_rules，涵蓋：非空、列表類型
            if "pre_process_rules" not in field.data or not isinstance(field.data["pre_process_rules"], list):
                raise ValidationError("pre_process_rules必須為列表")

            # 4.提取pre_process_rules中唯一的處理規則，避免重複處理
            unique_pre_process_rule_dict = {}
            for pre_process_rule in field.data["pre_process_rules"]:
                # 5.校驗id參數，非空、id規範
                if (
                        "id" not in pre_process_rule
                        or pre_process_rule["id"] not in ["remove_extra_space", "remove_url_and_email"]
                ):
                    raise ValidationError("預處理id格式錯誤")

                # 6.校驗enabled參數，涵蓋：非空、布林值
                if "enabled" not in pre_process_rule or not isinstance(pre_process_rule["enabled"], bool):
                    raise ValidationError("預處理enabled格式錯誤")

                # 7.將數據添加到唯一字典中，過濾無關的數據
                unique_pre_process_rule_dict[pre_process_rule["id"]] = {
                    "id": pre_process_rule["id"],
                    "enabled": pre_process_rule["enabled"],
                }

            # 8.判斷一下是否傳遞了兩個處理規則
            if len(unique_pre_process_rule_dict) != 2:
                raise ValidationError("預處理規則格式錯誤，請重試嘗試")

            # 9.將處理後的數據轉換成列表並覆蓋與處理規則
            field.data["pre_process_rules"] = list(unique_pre_process_rule_dict.values())

            # 10.校驗分段參數segment，涵蓋：非空、字典
            if "segment" not in field.data or not isinstance(field.data["segment"], dict):
                raise ValidationError("分段設置不能為空且為字典")

            # 11.校驗分隔符號separators，涵蓋：非空、列表、子元素為字串
            if "separators" not in field.data["segment"] or not isinstance(field.data["segment"]["separators"], list):
                raise ValidationError("分隔符號列表不能為空且為列表")
            for separator in field.data["segment"]["separators"]:
                if not isinstance(separator, str):
                    raise ValidationError("分隔符號列表元素類型錯誤")
            if len(field.data["segment"]["separators"]) == 0:
                raise ValidationError("分隔符號列表不能為空列表")

            # 12.校驗分塊大小chunk_size，涵蓋了：非空、數字、範圍
            if "chunk_size" not in field.data["segment"] or not isinstance(field.data["segment"]["chunk_size"], int):
                raise ValidationError("分割塊大小不能為空且為整數")
            if field.data["segment"]["chunk_size"] < 100 or field.data["segment"]["chunk_size"] > 1000:
                raise ValidationError("分割塊大小在100-1000")

            # 13.校驗塊重疊大小chunk_overlap，涵蓋：非空、數字、範圍
            if (
                    "chunk_overlap" not in field.data["segment"]
                    or not isinstance(field.data["segment"]["chunk_overlap"], int)
            ):
                raise ValidationError("塊重疊大小不能為空且為整數")
            if not (0 <= field.data["segment"]["chunk_overlap"] <= field.data["segment"]["chunk_size"] * 0.5):
                raise ValidationError(f"塊重疊大小在0-{int(field.data['segment']['chunk_size'] * 0.5)}")

            # 14.更新並提出多餘數據
            field.data = {
                "pre_process_rules": field.data["pre_process_rules"],
                "segment": {
                    "separators": field.data["segment"]["separators"],
                    "chunk_size": field.data["segment"]["chunk_size"],
                    "chunk_overlap": field.data["segment"]["chunk_overlap"],
                }
            }


class CreateDocumentsResp(Schema):
    """創建文件列表響應結構"""
    documents = fields.List(fields.Dict, dump_default=[])
    batch = fields.String(dump_default="")

    @pre_dump
    def process_data(self, data: tuple[list[Document], str], **kwargs):
        return {
            "documents": [{
                "id": document.id,
                "name": document.name,
                "status": document.status,
                "created_at": int(document.created_at.timestamp())
            } for document in data[0]],
            "batch": data[1],
        }


class GetDocumentResp(Schema):
    """獲取文件基礎資訊響應結構"""


class UpdateDocumentNameReq(FlaskForm):
    """更新檔案名稱/基礎資訊請求"""


class GetDocumentsWithPageReq(PaginatorReq):
    """獲取文件分頁列表請求"""


class GetDocumentsWithPageResp(Schema):
    """獲取文件分頁列表響應結構"""


class UpdateDocumentEnabledReq(FlaskForm):
    """更新文件啟用狀態請求"""
