#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/12/21 下午2:35
@Author : zsting29@gmail.com
@File   : router.py
"""

from dataclasses import dataclass

from flask import Flask, Blueprint
from injector import inject

from internal.handler import AppHandler, BulidinToolHandler, ApiToolHandler


@inject
@dataclass
class Router:
    """路由"""
    app_handler: AppHandler
    buildin_tool_handler: BulidinToolHandler
    api_tool_handler: ApiToolHandler

    # # 使用 @dataclass
    # def __init__(self, app_handler: AppHandler):
    #     self.app_handler = app_handler

    def register_router(self, app: Flask):
        """註冊路由"""
        # 1. 創建藍圖
        bp = Blueprint("llmops", __name__, url_prefix="")

        # 2. 將url與對應控制器方法做綁定
        bp.add_url_rule("/ping", view_func=self.app_handler.ping)
        bp.add_url_rule("/apps/<uuid:app_id>/debug", methods=["POST"], view_func=self.app_handler.debug)
        bp.add_url_rule("/app", methods=["POST"], view_func=self.app_handler.create_app)
        # bp.add_url_rule("/app/<uuid:id>", methods=["GET"], view_func=self.app_handler.get_app)
        # bp.add_url_rule("/app/<uuid:id>", methods=["POST"], view_func=self.app_handler.update_app)
        # bp.add_url_rule("/app/<uuid:id>/delete", methods=["POST"], view_func=self.app_handler.delete_app)

        # 內置插件廣場模塊
        bp.add_url_rule("/buildin-tools", view_func=self.buildin_tool_handler.get_buildin_tools)
        bp.add_url_rule(
            "/buildin-tools/<string:provider_name>/tools/<string:tool_name>",
            view_func=self.buildin_tool_handler.get_provider_tool
        )
        bp.add_url_rule(
            "/buildin-tools/<string:provider_name>/icon",
            view_func=self.buildin_tool_handler.get_provider_icon
        )
        bp.add_url_rule(
            "/buildin-tools/categories",
            view_func=self.buildin_tool_handler.get_categories
        )

        #  自定義API插件模塊
        bp.add_url_rule(
            "/api-tools",
            view_func=self.api_tool_handler.get_api_tool_providers_with_page,
        )
        bp.add_url_rule(
            "/api-tools/validate-openapi-schema",
            methods=["POST"],
            view_func=self.api_tool_handler.validate_openapi_schema
        )
        bp.add_url_rule(
            "/api-tools",
            methods=["POST"],
            view_func=self.api_tool_handler.create_api_tool
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            view_func=self.api_tool_handler.get_api_tool_provider
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>/tools/<string:tool_name>",
            view_func=self.api_tool_handler.get_api_tool
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>/delete",
            methods=["POST"],
            view_func=self.api_tool_handler.delete_api_tool_provider,
        )

        # 3.應用上去注冊藍圖
        app.register_blueprint(bp)

        # print(app.url_map)
