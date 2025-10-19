#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/10 下午11:12
@Author : zsting29@gmail.com
@File   : segment_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.segment_schema import (
    GetSegmentsWithPageReq,
    GetSegmentsWithPageResp,
    CreateSegmentReq, GetSegmentResp, UpdateSegmentEnabledReq, UpdateSegmentReq
)
from internal.service.segment_service import SegmentService
from pkg.paginator import PageModel
from pkg.response import (validate_error_json, success_json, success_message)


@inject
@dataclass
class SegmentHandler:
    """片段處理器"""
    segment_service: SegmentService

    @login_required
    def create_segment(self, dataset_id: UUID, document_id: UUID):
        """根據傳遞的資訊創建知識庫文件片段"""
        # 1.提取請求並校驗
        req = CreateSegmentReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建片段記錄
        self.segment_service.create_segment(dataset_id, document_id, req, current_user)

        return success_message("新增文件片段成功")

    @login_required
    def get_segments_with_page(self, dataset_id: UUID, document_id: UUID):
        """獲取指定知識庫文件的片段列表資訊"""
        # 1.提取請求並校驗
        req = GetSegmentsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務獲取片段列表+分頁數據
        segments, paginator = self.segment_service.get_segments_with_page(dataset_id, document_id, req, current_user)

        # 3.構建響應結構並返回
        resp = GetSegmentsWithPageResp(many=True)

        return success_json(
            PageModel(list=resp.dump(segments), paginator=paginator)
        )

    @login_required
    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """獲取指定的文件片段資訊詳情"""
        segment = self.segment_service.get_segment(dataset_id, document_id, segment_id, current_user)
        resp = GetSegmentResp()
        return success_json(resp.dump(segment))

    @login_required
    def update_segment_enabled(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """根據傳遞的資訊更新指定的文件片段啟用狀態"""
        # 1.提取請求並校驗
        req = UpdateSegmentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新文件片段的啟用狀態
        self.segment_service.update_segment_enabled(dataset_id, document_id, segment_id, req.enabled.data, current_user)

        return success_message("修改片段狀態成功")

    @login_required
    def delete_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """根據傳遞的資訊刪除指定的文件片段資訊"""
        self.segment_service.delete_segment(dataset_id, document_id, segment_id, current_user)
        return success_message("刪除文件片段成功")

    @login_required
    def update_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """根據傳遞的資訊刪除指定的文件片段資訊"""
        # 1.提取請求並校驗
        req = UpdateSegmentReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新文件片段資訊
        self.segment_service.update_segment(dataset_id, document_id, segment_id, req, current_user)

        return success_message("更新文件片段成功")
