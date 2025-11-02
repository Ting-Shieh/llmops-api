#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/10/26 上午11:59
@Author : zsting29@gmail.com
@File   : chat.py.py
"""
from langchain_openai import ChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOpenAI, BaseLanguageModel):
    """OpenAI聊天模型基類"""
    pass
