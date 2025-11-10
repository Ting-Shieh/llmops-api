#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/9 下午10:18
@Author : zsting29@gmail.com
@File   : bulidin_tool_handler.py
"""
import io
from dataclasses import dataclass

from flask import send_file
from flask_login import login_required
from injector import inject

from internal.service import BuildinToolService
from pkg.response import success_json


@inject
@dataclass
class BulidinToolHandler:
    """內置工具處理器"""
    buildin_tool_service: BuildinToolService

    @login_required
    def get_buildin_tools(self):
        """獲取LLMOps所有的內置工具訊息和提供商訊息"""
        buildin_tools = self.buildin_tool_service.get_buildin_tools()
        return success_json(buildin_tools)

    @login_required
    def get_provider_tool(self, provider_name: str, tool_name: str):
        """根據傳遞的提供商名稱和工具名稱獲取指定工具訊息"""
        buildin_tool = self.buildin_tool_service.get_provider_tools(provider_name, tool_name)
        return success_json(buildin_tool)

    def get_provider_icon(self, provider_name: str):
        """根據傳遞的提供商獲取icon圖標流訊息"""
        icon, mimetype = self.buildin_tool_service.get_provider_icon(provider_name)
        return send_file(
            io.BytesIO(icon),
            mimetype=mimetype,
            as_attachment=False,
            download_name=f"{provider_name}_icon.svg"
        )

    @login_required
    def get_categories(self):
        """獲取所有內置提供商的分類訊息"""
        categories = self.buildin_tool_service.get_categories()
        return success_json(categories)
