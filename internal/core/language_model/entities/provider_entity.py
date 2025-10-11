#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/1 上午10:18
@Author : zsting29@gmail.com
@File   : provider_entity.py
"""
import os.path
from typing import Optional, Type, Any, Union

import yaml
from pydantic.v1 import BaseModel, Field, root_validator

from internal.core.language_model.entities.default_model_parameter_template import DEFAULT_MODEL_PARAMETER_TEMPLATE
from internal.core.language_model.entities.model_entity import ModelEntity, ModelType, BaseLanguageModel
from internal.exception import NotFoundException, FailException
from internal.lib.helper import dynamic_import


class ProviderEntity(BaseModel):
    """模型提供商實體資訊"""
    name: str = ""  # 提供商的名字
    label: str = ""  # 提供商的標籤
    description: str = ""  # 提供商的描述資訊
    icon: str = ""  # 提供商的圖示
    background: str = ""  # 提供商的圖示背景
    supported_model_types: list[ModelType] = Field(default_factory=list)  # 支持的模型類型


class Provider(BaseModel):
    """大語言模型服務提供商，在該類下，可以獲取到該服務提供商的所有大語言模型、描述、圖示、標籤等多個資訊"""
    name: str  # 提供商名字
    position: int  # 服務提供商的位置資訊
    provider_entity: ProviderEntity  # 模型提供商實體
    model_entity_map: dict[str, ModelEntity] = Field(default_factory=dict)  # 模型實體映射
    model_class_map: dict[str, Union[None, Type[BaseLanguageModel]]] = Field(default_factory=dict)  # 模型類映射

    @root_validator(pre=False)
    def validate_provider(cls, provider: dict[str, Any]) -> dict[str, Any]:
        """服務提供者校驗器，利用校驗器完成該服務提供者的實體與類實例化"""
        # 1.獲取服務提供商實體
        provider_entity: ProviderEntity = provider["provider_entity"]

        # 2.動態導入服務提供商的模型類
        for model_type in provider_entity.supported_model_types:
            # 3.將類型的第一個字元轉換成大寫，其他不變，並構建類映射
            symbol_name = model_type[0].upper() + model_type[1:]
            provider["model_class_map"][model_type] = dynamic_import(
                f"internal.core.language_model.providers.{provider_entity.name}.{model_type}",
                symbol_name
            )

        # 4.獲取當前類所在的位置，provider提供商所在的位置
        current_path = os.path.abspath(__file__)
        entities_path = os.path.dirname(current_path)
        provider_path = os.path.join(os.path.dirname(entities_path), "providers", provider_entity.name)

        # 5.組裝positions.yaml的位置，並讀取數據
        positions_yaml_path = os.path.join(provider_path, "positions.yaml")
        with open(positions_yaml_path, encoding="utf-8") as f:
            positions_yaml_data = yaml.safe_load(f) or []
        if not isinstance(positions_yaml_data, list):
            raise FailException("positions.yaml數據格式錯誤")

        # 6.循環讀取位置中的模型名字
        for model_name in positions_yaml_data:
            # 7.組裝每一個模型的詳細資訊
            model_yaml_path = os.path.join(provider_path, f"{model_name}.yaml")
            with open(model_yaml_path, encoding="utf-8") as f:
                model_yaml_data = yaml.safe_load(f)

            # 8.循環讀取模型中的parameters參
            yaml_parameters = model_yaml_data.get("parameters")
            parameters = []
            for parameter in yaml_parameters:
                # 9.檢測參數規則是否使用了模板配置
                use_template = parameter.get("use_template")
                if use_template:
                    # 10.使用了模板，則使用模板補全剩餘數據，並刪除use_template
                    default_parameter = DEFAULT_MODEL_PARAMETER_TEMPLATE.get(use_template)
                    del parameter["use_template"]
                    parameters.append({**default_parameter, **parameter})
                else:
                    # 11.未使用模板，則直接添加
                    parameters.append(parameter)

            # 12.修改對應模板的yaml數據，並創建ModelEntity隨後傳遞給provider
            model_yaml_data["parameters"] = parameters
            provider["model_entity_map"][model_name] = ModelEntity(**model_yaml_data)

        return provider

    def get_model_class(self, model_type: ModelType) -> Optional[Type[BaseLanguageModel]]:
        """根據傳遞的模型類型獲取該提供者的模型類"""
        model_class = self.model_class_map.get(model_type, None)
        if model_class is None:
            raise NotFoundException("該模型實體不存在，請核實後重試")
        return model_class

    def get_model_entity(self, model_name: str) -> Optional[ModelEntity]:
        """根據傳遞的模型名字獲取模型實體資訊"""
        model_entity = self.model_entity_map.get(model_name, None)
        if model_entity is None:
            raise NotFoundException("該模型實體不存在，請核實後重試")
        return model_entity

    def get_model_entities(self) -> list[ModelEntity]:
        """獲取該服務提供者的所有模型實體列表資訊"""
        return list(self.model_entity_map.values())
