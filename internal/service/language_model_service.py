#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/31 下午11:17
@Author : zsting29@gmail.com
@File   : language_model_service.py
"""
import logging
from dataclasses import dataclass
from typing import Any

from injector import inject

from internal.core.language_model import LanguageModelManager
from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class LanguageModelService(BaseService):
    """語言模型服務"""
    db: SQLAlchemy
    language_model_manager: LanguageModelManager

    def load_language_model(self, model_config: dict[str, Any]) -> BaseLanguageModel:
        """根據傳遞的模型配置載入大語言模型，並返回其實例"""
        try:
            # 1.從model_config中提取出provider、model、parameters
            provider_name = model_config.get("provider", "")
            model_name = model_config.get("model", "")
            parameters = model_config.get("parameters", {})

            # 2.從模型管理器獲取提供者、模型實體、模型類
            provider = self.language_model_manager.get_provider(provider_name)
            model_entity = provider.get_model_entity(model_name)
            model_class = provider.get_model_class(model_entity.model_type)

            # 3.實例化模型後並返回
            return model_class(
                **model_entity.attributes,
                **parameters,
                features=model_entity.features,
                metadata=model_entity.metadata,
            )
        except Exception as error:
            logging.error("獲取模型失敗, 錯誤資訊: $(error)s", {"error": error}, exc_info=True)
            return self.load_default_language_model()

    def load_default_language_model(self) -> BaseLanguageModel:
        """載入預設的大語言模型，在模型管理器中獲取不到模型或者出錯時使用默認模型進行兜底"""
        # 1.獲取openai服務提供者與模型類
        provider = self.language_model_manager.get_provider("openai")
        model_entity = provider.get_model_entity("gpt-4o-mini")
        model_class = provider.get_model_class(model_entity.model_type)

        # bug:原先寫法使用的是LangChain封裝的LLM類，需要替換成自訂封裝的類，否則會識別到模型不存在features
        # return ChatOpenAI(model="gpt-4o-mini", temperature=1, max_tokens=8192)

        # 2.實例化模型並返回
        return model_class(
            **model_entity.attributes,
            temperature=1,
            max_tokens=8192,
            features=model_entity.features,
            metadata=model_entity.metadata,
        )
