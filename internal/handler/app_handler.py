#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午2:30
@Author : zsting29@gmail.com
@File   : app_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.core.tools.buildin_tools.providers import BuildinProviderManager
from internal.schema.app_schema import (
    CreateAppReq,
    UpdateAppReq,
    GetAppResp,
    GetAppsWithPageResp,
    GetAppsWithPageReq, FallbackHistoryToDraftReq, GetPublishHistoriesWithPageReq, GetPublishHistoriesWithPageResp,
    UpdateDebugConversationSummaryReq, DebugChatReq, GetDebugConversationMessagesWithPageReq,
    GetDebugConversationMessagesWithPageResp
)
from internal.service import (
    AppService,
    VectorDatabaseService,
    ApiToolService,
    ConversationService
)
from pkg.paginator import PageModel
from pkg.response import (
    success_json,
    validate_error_json,
    success_message,
    compact_generate_response
)


@inject
@dataclass
class AppHandler:
    """應用控制器"""
    app_service: AppService
    vector_database_service: VectorDatabaseService
    buildin_provider_manager: BuildinProviderManager
    api_tool_service: ApiToolService
    conversation_service: ConversationService

    @login_required
    def create_app(self):
        """調用服務創建新的App紀錄"""
        # 1.提取請求並校驗
        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務創建應用資訊
        app = self.app_service.create_app(req, current_user)

        # 3.返回創建成功響應提示
        return success_json({"id": app.id})

    @login_required
    def get_app(self, app_id: UUID):
        """獲取指定的應用基礎資訊"""
        app = self.app_service.get_app(app_id, current_user)
        resp = GetAppResp()
        return success_json(resp.dump(app))

    # Todo
    @login_required
    def update_app(self, app_id: UUID):
        """根據傳遞的資訊更新指定的應用"""
        # 1.提取數據並校驗
        req = UpdateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新數據
        self.app_service.update_app(app_id, current_user, **req.data)

        return success_message("修改Agent智慧體應用成功")

    # Todo
    @login_required
    def delete_app(self, app_id: UUID):
        """根據傳遞的資訊刪除指定的應用"""
        self.app_service.delete_app(app_id, current_user)
        return success_message("刪除Agent智慧體應用成功")

    @login_required
    def get_apps_with_page(self):
        """獲取當前登入帳號的應用分頁列表數據"""
        # 1.提取數據並校驗
        req = GetAppsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務獲取列表數據以及分頁器
        apps, paginator = self.app_service.get_apps_with_page(req, current_user)

        # 3.構建響應結構並返回
        resp = GetAppsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(apps), paginator=paginator))

    @login_required
    def get_draft_app_config(self, app_id: UUID):
        """根據傳遞的應用id獲取應用的最新草稿配置"""
        draft_config = self.app_service.get_draft_app_config(app_id, current_user)
        return success_json(draft_config)

    @login_required
    def update_draft_app_config(self, app_id: UUID):
        """根據傳遞的應用id+草稿配置更新應用的最新草稿配置"""
        # 1.獲取草稿請求json數據
        draft_app_config = request.get_json(force=True, silent=True) or {}

        # 2.調用服務更新應用的草稿配置
        self.app_service.update_draft_app_config(app_id, draft_app_config, current_user)

        return success_message("更新應用草稿配置成功")

    @login_required
    def publish(self, app_id: UUID):
        """根據傳遞的應用id發布/更新特定的草稿配置資訊"""
        self.app_service.publish_draft_app_config(app_id, current_user)
        return success_message("發布/更新應用配置成功")

    @login_required
    def cancel_publish(self, app_id: UUID):
        """根據傳遞的應用id，取消發布指定的應用配置資訊"""
        self.app_service.cancel_publish_app_config(app_id, current_user)
        return success_message("取消發布應用配置成功")

    @login_required
    def fallback_history_to_draft(self, app_id: UUID):
        """根據傳遞的應用id+歷史配置版本id，退回指定版本到草稿中"""
        # 1.提取數據並校驗
        req = FallbackHistoryToDraftReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務回退指定版本到草稿
        self.app_service.fallback_history_to_draft(app_id, req.app_config_version_id.data, current_user)

        return success_message("回退歷史配置至草稿成功")

    @login_required
    def get_publish_histories_with_page(self, app_id: UUID):
        """根據傳遞的應用id，獲取應用發布歷史列表"""
        # 1.獲取請求數據並校驗
        req = GetPublishHistoriesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務獲取分頁列表數據
        app_config_versions, paginator = self.app_service.get_publish_histories_with_page(app_id, req, current_user)

        # 3.創建響應結構並返回
        resp = GetPublishHistoriesWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(app_config_versions), paginator=paginator))

    @login_required
    def get_debug_conversation_summary(self, app_id: UUID):
        """根據傳遞的應用id獲取除錯會話長期記憶"""
        summary = self.app_service.get_debug_conversation_summary(app_id, current_user)
        return success_json({"summary": summary})

    @login_required
    def update_debug_conversation_summary(self, app_id: UUID):
        """根據傳遞的應用id+摘要資訊更新除錯會話長期記憶"""
        # 1.提取數據並校驗
        req = UpdateDebugConversationSummaryReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務更新除錯會話長期記憶
        self.app_service.update_debug_conversation_summary(app_id, req.summary.data, current_user)

        return success_message("更新AI應用長期記憶成功")

    @login_required
    def delete_debug_conversation(self, app_id: UUID):
        """根據傳遞的應用id，清空該應用的除錯會話記錄"""
        self.app_service.delete_debug_conversation(app_id, current_user)
        return success_message("清空應用除錯會話記錄成功")

    @login_required
    def debug_chat(self, app_id: UUID):
        """根據傳遞的應用id+query，發起除錯對話"""
        # 1.提取數據並校驗數據
        req = DebugChatReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務發起會話除錯
        response = self.app_service.debug_chat(app_id, req, current_user)

        return compact_generate_response(response)

    @login_required
    def stop_debug_chat(self, app_id: UUID, task_id: UUID):
        """根據傳遞的應用id+任務id停止某個應用的指定除錯會話"""
        self.app_service.stop_debug_chat(app_id, task_id, current_user)
        return success_message("停止應用除錯會話成功")

    @login_required
    def get_debug_conversation_messages_with_page(self, app_id: UUID):
        """根據傳遞的應用id，獲取該應用的除錯會話分頁列表記錄"""
        # 1.提取請求並校驗數據
        req = GetDebugConversationMessagesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.調用服務獲取數據
        messages, paginator = self.app_service.get_debug_conversation_messages_with_page(app_id, req, current_user)

        # 3.創建響應結構
        resp = GetDebugConversationMessagesWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(messages), paginator=paginator))

    @login_required
    def get_published_config(self, app_id: UUID):
        """根據傳遞的應用id獲取應用的發布配置資訊"""
        published_config = self.app_service.get_published_config(app_id, current_user)
        return success_json(published_config)

    @login_required
    def regenerate_web_app_token(self, app_id: UUID):
        """根據傳遞的應用id重新生成WebApp憑證標識"""
        token = self.app_service.regenerate_web_app_token(app_id, current_user)
        return success_json({"token": token})

    @login_required
    def ping(self):
        pass
        # conversation_name = self.conversation_service.generate_conversation_name("我喜歡作詞作曲")
        # return success_json({"conversation_name": conversation_name})

        # google_serper = self.buildin_provider_manager.get_tool(provider_name="google", tool_name="google_serper")()
        # print(google_serper)
        # print(google_serper.invoke("今天台積電最高股價是多少？"))

        # google = self.buildin_provider_manager.get_provider("google")
        # google_serper_entity = google.get_tool_entity("google_serper")
        # print(google_serper_entity)

        # 獲取所有服務提供商
        # providers = self.buildin_provider_manager.get_provider＿entities()
        #
        # return success_json({"providers": [provider.dict() for provider in providers]})
        # demo_task.delay(uuid.uuid4())
        # return self.api_tool_service.api_tool_invoke()

        # return {"ping": "pong"}
