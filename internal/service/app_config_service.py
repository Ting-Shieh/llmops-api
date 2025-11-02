#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/25 下午12:49
@Author : zsting29@gmail.com
@File   : app_config_service.py
"""
from dataclasses import dataclass
from typing import Any, Union

from injector import inject
from langchain_core.tools import BaseTool

from internal.core.language_model.entities.model_entity import ModelParameterType
from internal.core.language_model.language_model_manager import LanguageModelManager
from internal.core.tools.api_tools.providers import ApiProviderManager
from internal.core.tools.buildin_tools.providers import BuildinProviderManager
from internal.entity.app_entity import DEFAULT_APP_CONFIG
from internal.lib.helper import get_value_type, datetime_to_timestamp
from internal.model import App, ApiTool, Dataset, AppConfig, AppConfigVersion
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..core.tools.api_tools.entities import ToolEntity


@inject
@dataclass
class AppConfigService(BaseService):
    """应用配置服务"""
    db: SQLAlchemy
    api_provider_manager: ApiProviderManager
    builtin_provider_manager: BuildinProviderManager
    language_model_manager: LanguageModelManager

    def get_draft_app_config(self, app: App) -> dict[str, Any]:
        """根據傳遞的應用獲取該應用的草稿配置"""
        # 1.提取應用的草稿配置
        draft_app_config = app.draft_app_config

        # todo:校驗model_config資訊 => 等多LLM模組引入在完善
        # # 2.校驗model_config資訊，如果使用了不存在的提供者或者模型，則使用預設值(寬鬆校驗)
        # validate_model_config = self._process_and_validate_model_config(draft_app_config.model_config)
        # if draft_app_config.model_config != validate_model_config:
        #     self.update(draft_app_config, model_config=validate_model_config)

        # 3.循環遍歷工具列表刪除已經被刪除的工具資訊
        tools, validate_tools = self._process_and_validate_tools(draft_app_config.tools)

        # 4.判斷是否需要更新草稿配置中的工具列表資訊
        if draft_app_config.tools != validate_tools:
            # 14.更新草稿配置中的工具列表
            self.update(draft_app_config, tools=validate_tools)

        # 5.校驗知識庫列表，如果引用了不存在/被刪除的知識庫，需要剔除數據並更新，同時獲取知識庫的額外資訊
        datasets, validate_datasets = self._process_and_validate_datasets(draft_app_config.datasets)

        # 6.判斷是否存在已刪除的知識庫，如果存在則更新
        if set(validate_datasets) != set(draft_app_config.datasets):
            self.update(draft_app_config, datasets=validate_datasets)

        # todo: 校驗工作流列表對應的數據
        workflows = []
        # # 7.校驗工作流列表對應的數據
        # workflows, validate_workflows = self._process_and_validate_workflows(draft_app_config.workflows)
        # if set(validate_workflows) != set(draft_app_config.workflows):
        #     self.update(draft_app_config, workflows=validate_workflows)

        # 20.將數據轉換成字典後返回
        validate_model_config = {}
        return self._process_and_transformer_app_config(
            validate_model_config,
            tools,
            workflows,
            datasets,
            draft_app_config,
        )

    def get_langchain_tools_by_tools_config(
            self,
            tools_config: list[dict]
    ) -> list[BaseTool]:
        """根據傳遞的工具配置列表獲取langchain工具列表"""
        # 1.循環遍歷所有工具配置列表資訊
        tools = []
        for tool in tools_config:
            # 2.根據不同的工具類型執行不同的操作
            if tool["type"] == "builtin_tool":
                # 3.內建工具，通過builtin_provider_manager獲取工具實例
                builtin_tool = self.builtin_provider_manager.get_tool(
                    tool["provider"]["id"],
                    tool["tool"]["name"]
                )
                if not builtin_tool:
                    continue
                tools.append(builtin_tool(**tool["tool"]["params"]))
            else:
                # 4.API工具，首先根據id找到ApiTool記錄，然後創建範例
                api_tool = self.get(ApiTool, tool["tool"]["id"])
                if not api_tool:
                    continue
                tools.append(
                    self.api_provider_manager.get_tool(
                        ToolEntity(
                            id=str(api_tool.id),
                            name=api_tool.name,
                            url=api_tool.url,
                            method=api_tool.method,
                            description=api_tool.description,
                            headers=api_tool.provider.headers,
                            parameters=api_tool.parameters,
                        )
                    )
                )

        return tools

    @classmethod
    def _process_and_transformer_app_config(
            cls,
            model_config: dict[str, Any],
            tools: list[dict],
            workflows: list[dict],
            datasets: list[dict],
            app_config: Union[AppConfig, AppConfigVersion]
    ) -> dict[str, Any]:
        """根據傳遞的插件列表、工作流列表、知識庫列表以及應用配置創建字典資訊"""
        return {
            "id": str(app_config.id),
            "model_config": model_config,
            "dialog_round": app_config.dialog_round,
            "preset_prompt": app_config.preset_prompt,
            "tools": tools,
            "workflows": workflows,
            "datasets": datasets,
            "retrieval_config": app_config.retrieval_config,
            "long_term_memory": app_config.long_term_memory,
            "opening_statement": app_config.opening_statement,
            "opening_questions": app_config.opening_questions,
            "speech_to_text": app_config.speech_to_text,
            "text_to_speech": app_config.text_to_speech,
            "suggested_after_answer": app_config.suggested_after_answer,
            "review_config": app_config.review_config,
            "updated_at": datetime_to_timestamp(app_config.updated_at),
            "created_at": datetime_to_timestamp(app_config.created_at),
        }

    def _process_and_validate_datasets(self, origin_datasets: list[dict]) -> tuple[list[dict], list[dict]]:
        """根據傳遞的知識庫並返回知識庫配置與校驗後的數據"""
        # 1.校驗知識庫配置列表，如果引用了不存在的/被刪除的知識庫，則需要剔除數據並更新，同時獲取知識庫的額外資訊
        datasets = []
        dataset_records = self.db.session.query(Dataset).filter(Dataset.id.in_(origin_datasets)).all()
        dataset_dict = {str(dataset_record.id): dataset_record for dataset_record in dataset_records}
        dataset_sets = set(dataset_dict.keys())

        # 2.計算存在的知識庫id列表，為了保留原始順序，使用列表循環的方式來判斷
        validate_datasets = [dataset_id for dataset_id in origin_datasets if dataset_id in dataset_sets]

        # 3.循環獲取知識庫數據
        for dataset_id in validate_datasets:
            dataset = dataset_dict.get(str(dataset_id))
            datasets.append({
                "id": str(dataset.id),
                "name": dataset.name,
                "icon": dataset.icon,
                "description": dataset.description,
            })

        return datasets, validate_datasets

    def _process_and_validate_tools(self, origin_tools: list[dict]) -> tuple[list[dict], list[dict]]:
        """根據傳遞的原始工具資訊進行處理和校驗"""
        # 1.循環遍歷工具列表刪除已被刪除的工具
        validate_tools = []
        tools = []
        for tool in origin_tools:
            if tool["type"] == "builtin_tool":
                # 2.查詢內建工具提供者，並檢測是否存在
                provider = self.builtin_provider_manager.get_provider(tool["provider_id"])
                if not provider:
                    continue

                # 3.獲取提供者下的工具實體，並檢測是否存在
                tool_entity = provider.get_tool_entity(tool["tool_id"])
                if not tool_entity:
                    # 代表被刪除
                    continue

                # 4.判斷工具的params(.yaml檔)和草稿中的params是否一致，如果不一致則全部重設為預設值（或者考慮刪除這個工具的引用）
                param_keys = set([param.name for param in tool_entity.params])
                params = tool["params"]
                if set(tool["params"].keys()) - param_keys:
                    params = {
                        param.name: param.default
                        for param in tool_entity.params
                        if param.default is not None
                    }

                # 5.數據都存在，並且參數已經校驗完畢，可以將數據添加到validate_tools
                validate_tools.append({**tool, "params": params})

                # 6.組裝內建工具展示資訊
                provider_entity = provider.provider_entity
                tools.append({
                    "type": "builtin_tool",
                    "provider": {
                        "id": provider_entity.name,
                        "name": provider_entity.name,
                        "label": provider_entity.label,
                        "icon": f"/api/builtin-tools/{provider_entity.name}/icon",
                        "description": provider_entity.description,
                    },
                    "tool": {
                        "id": tool_entity.name,
                        "name": tool_entity.name,
                        "label": tool_entity.label,
                        "description": tool_entity.description,
                        "params": tool["params"],
                    }
                })
            elif tool["type"] == "api_tool":
                # 7.查詢資料庫獲取對應的工具記錄，並檢測是否存在
                tool_record = self.db.session.query(ApiTool).filter(
                    ApiTool.provider_id == tool["provider_id"],
                    ApiTool.name == tool["tool_id"],
                ).one_or_none()
                if not tool_record:
                    continue

                # 8.數據校驗通過，往validate_tools中添加數據
                validate_tools.append(tool)

                # 9.組裝api工具展示資訊
                provider = tool_record.provider
                tools.append({
                    "type": "api_tool",
                    "provider": {
                        "id": str(provider.id),
                        "name": provider.name,
                        "label": provider.name,
                        "icon": provider.icon,
                        "description": provider.description,
                    },
                    "tool": {
                        "id": str(tool_record.id),
                        "name": tool_record.name,
                        "label": tool_record.name,
                        "description": tool_record.description,
                        "params": {},
                    },
                })

        return tools, validate_tools

    def _process_and_validate_model_config(self, origin_model_config: dict[str, Any]) -> dict[str, Any]:
        """根據傳遞的模型配置處理並校驗，隨後返回校驗後的資訊"""
        # 1.判斷model_config是否為字典，如果不是則直接返回預設值
        if not isinstance(origin_model_config, dict):
            return DEFAULT_APP_CONFIG["model_config"]

        # 2.提取origin_model_config中provider、model、parameters對應的資訊
        model_config = {
            "provider": origin_model_config.get("provider", ""),
            "model": origin_model_config.get("model", ""),
            "parameters": origin_model_config.get("parameters", {}),
        }

        # 3.判斷provider是否存在、類型是否正確，如果不符合規則則返回預設值
        if not model_config["provider"] or not isinstance(model_config["provider"], str):
            return DEFAULT_APP_CONFIG["model_config"]
        provider = self.language_model_manager.get_provider(model_config["provider"])
        if not provider:
            return DEFAULT_APP_CONFIG["model_config"]

        # 4.判斷model是否存在、類型是否正確，如果不符合則返回預設值
        if not model_config["model"] or not isinstance(model_config["model"], str):
            return DEFAULT_APP_CONFIG["model_config"]
        model_entity = provider.get_model_entity(model_config["model"])
        if not model_entity:
            return DEFAULT_APP_CONFIG["model_config"]

        # 5.判斷parameters資訊類型是否錯誤，如果錯誤則設置為預設值
        if not isinstance(model_config["parameters"], dict):
            model_config["parameters"] = {
                parameter.name: parameter.default for parameter in model_entity.parameters
            }

        # 6.剔除傳遞的多餘的parameter，亦或者是少傳遞的參數使用預設值補上
        parameters = {}
        for parameter in model_entity.parameters:
            # 7.從model_config中獲取參數值，如果不存在則設置為預設值
            parameter_value = model_config["parameters"].get(parameter.name, parameter.default)

            # 8.判斷參數是否必填
            if parameter.required:
                # 9.參數必填，則值不允許為None，如果為None則設置預設值
                if parameter_value is None:
                    parameter_value = parameter.default
                else:
                    # 10.值非空則校驗數據類型是否正確，不正確則設置預設值
                    if get_value_type(parameter_value) != parameter.type.value:
                        parameter_value = parameter.default
            else:
                # 11.參數非必填，數據非空的情況下需要校驗
                if parameter_value is not None:
                    if get_value_type(parameter_value) != parameter.type.value:
                        parameter_value = parameter.default

            # 12.判斷參數是否存在options，如果存在則數值必須在options中選擇
            if parameter.options and parameter_value not in parameter.options:
                parameter_value = parameter.default

            # 13.參數類型為int/float，如果存在min/max時候需要校驗
            if parameter.type in [ModelParameterType.INT, ModelParameterType.FLOAT] and parameter_value is not None:
                # 14.校驗數值的min/max
                if (
                        (parameter.min and parameter_value < parameter.min)
                        or (parameter.max and parameter_value > parameter.max)
                ):
                    parameter_value = parameter.default

            parameters[parameter.name] = parameter_value

        # 15.完成數據校驗，賦值parameters參數
        model_config["parameters"] = parameters

        return model_config

    # def _process_and_validate_workflows(self, origin_workflows: list[UUID]) -> tuple[list[dict], list[UUID]]:
    #     """根據傳遞的工作流列表並返回工作流配置和校驗後的數據"""
    #     # 1.校驗工作流配置列表，如果引用了不存在/被刪除的工作流，則需要提出數據並更新，同時獲取工作流的額外資訊
    #     workflows = []
    #     workflow_records = self.db.session.query(Workflow).filter(
    #         Workflow.id.in_(origin_workflows),
    #         Workflow.status == WorkflowStatus.PUBLISHED,
    #     ).all()
    #     workflow_dict = {str(workflow_record.id): workflow_record for workflow_record in workflow_records}
    #     workflow_sets = set(workflow_dict.keys())
    #
    #     # 2.計算存在的工作流id列表，為了保留原始順序，使用列表循環的方式來判斷
    #     validate_workflows = [workflow_id for workflow_id in origin_workflows if workflow_id in workflow_sets]
    #
    #     # 3.循環獲取工作流數據
    #     for workflow_id in validate_workflows:
    #         workflow = workflow_dict.get(str(workflow_id))
    #         workflows.append({
    #             "id": str(workflow.id),
    #             "name": workflow.name,
    #             "icon": workflow.icon,
    #             "description": workflow.description,
    #         })
    #
    #     return workflows, validate_workflows
