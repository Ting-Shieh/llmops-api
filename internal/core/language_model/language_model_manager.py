#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/1 上午10:15
@Author : zsting29@gmail.com
@File   : language_model_manager.py
"""
import os.path
from typing import Any, Optional, Type

import yaml
from injector import inject, singleton
from langchain_core.pydantic_v1 import (
    BaseModel,
    Field,
    root_validator
)

from internal.core.language_model.entities.model_entity import (
    ModelType,
    BaseLanguageModel
)
from internal.core.language_model.entities.provider_entity import (
    Provider,
    ProviderEntity
)
from internal.exception import NotFoundException


@inject
@singleton
class LanguageModelManager(BaseModel):
    """语言模型管理器"""
    provider_map: dict[str, Provider] = Field(default_factory=dict)  # 服务提供者映射

    @root_validator(pre=False)
    def validate_language_model_manager(cls, values: dict[str, Any]) -> dict[str, Any]:
        """使用pydantic提供的預設規則校驗提供者映射，完成語言模型管理器的初始化"""
        # 1.獲取當前類所在的路徑
        current_path = os.path.abspath(__file__)
        providers_path = os.path.join(os.path.dirname(current_path), "providers")
        providers_yaml_path = os.path.join(providers_path, "providers.yaml")

        # 2.讀取providers.yaml數據配置獲取提供者列表
        with open(providers_yaml_path, encoding="utf-8") as f:
            providers_yaml_data = yaml.safe_load(f)

        # 3.循環讀取服務提供者數據並配置模型資訊
        values["provider_map"] = {}
        for index, provider_yaml_data in enumerate(providers_yaml_data):
            # 4.獲取提供者實體數據結構，並構建服務提供者實體
            provider_entity = ProviderEntity(**provider_yaml_data)
            values["provider_map"][provider_entity.name] = Provider(
                name=provider_entity.name,
                position=index + 1,
                provider_entity=provider_entity,
            )
        return values

    def get_provider(self, provider_name: str) -> Optional[Provider]:
        """根據傳遞的提供者名字獲取提供者"""
        provider = self.provider_map.get(provider_name, None)
        if provider is None:
            raise NotFoundException("該模型服務提供商不存在，請核實後重試")
        return provider

    def get_providers(self) -> list[Provider]:
        """獲取所有提供者列表資訊"""
        return list(self.provider_map.values())

    def get_model_class_by_provider_and_type(
            self,
            provider_name: str,
            model_type: ModelType,
    ) -> Optional[Type[BaseLanguageModel]]:
        """根據傳遞的提供者名字+模型類型，獲取模型類"""
        provider = self.get_provider(provider_name)

        return provider.get_model_class(model_type)

    def get_model_class_by_provider_and_model(
            self,
            provider_name: str,
            model_name: str,
    ) -> Optional[Type[BaseLanguageModel]]:
        """根據傳遞的提供者名字+模型名字獲取模型類"""
        # 1.根據名字獲取提供者資訊
        provider = self.get_provider(provider_name)

        # 2.在提供者下獲取該模型實體
        model_entity = provider.get_model_entity(model_name)

        return provider.get_model_class(model_entity.model_type)
