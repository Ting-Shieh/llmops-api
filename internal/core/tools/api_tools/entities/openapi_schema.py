#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/12 下午11:26
@Author : zsting29@gmail.com
@File   : openapi_schema.py
"""
from enum import Enum

from pydantic import BaseModel, Field
from pydantic import field_validator

from internal.exception import ValidateErrorException


class ParameterIn(str, Enum):
    """參數支持存放的位置"""
    PATH: str = "path"
    QUERY: str = "query"
    HEADER: str = "header"
    COOKIE: str = "cookie"
    REQUEST_BODY: str = "request_body"


class ParameterType(str, Enum):
    """參數支持的類型"""
    STR: str = "str"
    INT: str = "int"
    FLOAT: str = "float"
    BOOL: str = "bool"


ParameterTypeMap = {
    ParameterType.STR: "str",
    ParameterType.INT: "int",
    ParameterType.FLOAT: "float",
    ParameterType.BOOL: "bool",
}


class OpenAPISchema(BaseModel):
    """OpenAPI規範的JSON"""
    server: str = Field(
        default="",
        validate_default=True,
        description="工具提供商的服務基礎地址"
    )
    description: str = Field(
        default="",
        validate_default=True,
        description="工具提供商的描述訊息"
    )
    paths: dict[str, dict] = Field(
        default_factory=dict,
        validate_default=True,
        description="工具提供商的路徑參數字典"
    )

    @field_validator("server", mode="before")
    def validate_server(cls, server: str) -> str:
        """效驗server數據"""
        if server is None or server == "":
            raise ValidateErrorException("server不能為空且為字符串")
        return server

    @field_validator("description", mode="before")
    def validate_description(cls, description: str) -> str:
        """效驗server數據"""
        if description is None or description == "":
            raise ValidateErrorException("description不能為空且為字符串")
        return description

    @field_validator("paths", mode="before")
    def validate_paths(cls, paths: dict[str, dict]) -> dict[str, dict]:
        """效驗paths數據，涵蓋：方法提取，operationId唯一標誌，parameters校驗"""
        # 1.paths不能為空且類型為字典
        if not paths or not isinstance(paths, dict):
            raise ValidateErrorException("openapi_schema中的paths不能為空且必須為字典")

        # 2.提取paths裡的每一個元素，並獲取元素下的get/post方法對應值
        methods = ["get", "post"]
        interfaces = []
        extra_paths = {}
        for path, path_item in paths.items():
            for method in methods:
                # 3.檢測是否存在特定的方法並提取訊息
                interfaces.append({
                    "path": path,
                    "method": method,
                    "operation": path_item[method]
                })
        # 4.遍歷提取到的所有接口並校驗訊息，涵蓋operationId唯一標誌，parameters參數
        operation_ids = []
        for interface in interfaces:
            # 5.校驗description/operationId/parameters字段
            if not isinstance(interface["operation"].get("description"), str):
                raise ValidateErrorException("description不能為空且為字符串")
            if not isinstance(interface["operation"].get("operationId"), str):
                raise ValidateErrorException("operationId不能為空且為字符串")
            if not isinstance(interface["operation"].get("parameters", []), list):
                raise ValidateErrorException("parameters不能為列表或空")

            # 6.檢測operationId是否是唯一的
            if interface["operation"]["operationId"] in operation_ids:
                raise ValidateErrorException(f"operationId必須是唯一，{interface['operation']['operationId']}出現重複")
            operation_ids.append(interface["operation"]["operationId"])

            # 7.校驗parameters參數格式是否正確
            for parameter in interface["operation"].get("parameters", []):
                # 8.校驗 name / in / description / required / type 參數是否存在，並且正確
                if not isinstance(parameter.get("name"), str):
                    raise ValidateErrorException("parameter.name不能為空且為字符串")
                if not isinstance(parameter.get("description"), str):
                    raise ValidateErrorException("parameter.description不能為空且為字符串")
                if not isinstance(parameter.get("required"), bool):
                    raise ValidateErrorException("parameter.required不能為空且為布爾值")
                if (
                        not isinstance(parameter.get("in"), str)
                        or parameter.get("in") not in ParameterIn.__members__.values()
                ):
                    raise ValidateErrorException(
                        f"parameter.in參數必須為{'/'.join([item.value for item in ParameterIn])}不能為空且為字符串"
                    )
                if (
                        not isinstance(parameter.get("type"), str)
                        or parameter.get("type") not in ParameterType.__members__.values()
                ):
                    raise ValidateErrorException(
                        f"parameter.type參數必須為{'/'.join([item.value for item in ParameterType])}不能為空且為字符串"
                    )

            # 9.組裝數據並更新
            extra_paths[interface["path"]] = {
                interface["method"]: {
                    "description": interface["operation"]["description"],
                    "operationId": interface["operation"]["operationId"],
                    "parameters": [{
                        "name": parameter.get("name"),
                        "in": parameter.get("in"),
                        "description": parameter.get("description"),
                        "required": parameter.get("required"),
                        "type": parameter.get("type")
                    } for parameter in interface["operation"].get("parameters", [])],
                }
            }

        return extra_paths
