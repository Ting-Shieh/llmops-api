#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/21 下午10:38
@Author : zsting29@gmail.com
@File   : api_provider_manager.py
"""
from dataclasses import dataclass
from typing import Type, Optional, Callable

import requests
from injector import inject
from langchain_core.pydantic_v1 import BaseModel, create_model, Field
from langchain_core.tools import BaseTool, StructuredTool

from internal.core.tools.api_tools.entities import ToolEntity, ParameterTypeMap, ParameterIn


@inject
@dataclass
class ApiProviderManager(BaseModel):
    """API工具提供者管理器，能根據傳遞的工具配置訊息生成自定義LangChain工具"""

    @classmethod
    def _create_tool_func_from_tool_entity(cls, tool_entity: ToolEntity) -> Callable:
        """根據傳遞的訊息創建發起API請求函數"""

        def tool_func(**kwargs) -> str:
            """API工具請求函數"""
            # 1.定義變量存儲來自path/query/cookie/request_body中的數據
            parameters = {
                ParameterIn.PATH: {},
                ParameterIn.QUERY: {},
                ParameterIn.HEADER: {},
                ParameterIn.COOKIE: {},
                ParameterIn.REQUEST_BODY: {},
            }

            # 2.更改參數結構映射
            parameter_map = {parameter.get("name"): parameter for parameter in tool_entity.parameters}
            header_map = {header.get("key"): header.get("value") for header in tool_entity.headers}

            # 3.循環遍歷傳遞所有字段並校驗
            for key, value in kwargs.items():
                # 4.提取鍵值對關聯的字段並校驗
                parameter = parameter_map.get(key)
                if parameter is None:
                    continue

                # 5.將參數存儲到合適的位置上，默認在query上
                parameters[parameter.get("in", ParameterIn.QUERY)][key] = value

            # 6.構建request請求並返回採集的內容
            return requests.request(
                method=tool_entity.method,
                url=tool_entity.url.format(**parameters[ParameterIn.PATH]),
                params=parameters[ParameterIn.QUERY],
                json=parameters[ParameterIn.REQUEST_BODY],
                headers={**header_map, **parameters[ParameterIn.HEADER]},
                cookies=parameters[ParameterIn.COOKIE]
            ).text

        return tool_func

    @classmethod
    def _create_model_from_parameters(cls, parameters: list[dict]) -> Type[BaseModel]:
        """根據傳遞的parameters參數創建BaseModel子類"""
        fields = {}
        for parameter in parameters:
            field_name = parameter.get("name")
            field_type = ParameterTypeMap.get(parameter.get("type"), str)
            field_required = parameter.get("required", True)
            field_description = parameter.get("description", "")

            fields[field_name] = (
                field_type if field_required else Optional[field_type],
                Field(description=field_description)
            )

        return create_model("DynamicModel", **fields)

    def get_tool(self, tool_entity: ToolEntity) -> BaseTool:
        """根據傳遞的配置獲取自定義API工具"""
        return StructuredTool.from_function(
            func=self._create_tool_func_from_tool_entity(tool_entity),
            name=f"{tool_entity.id}_{tool_entity.name}",
            description=tool_entity.description,
            args_schema=self._create_model_from_parameters(tool_entity.parameters),
        )
