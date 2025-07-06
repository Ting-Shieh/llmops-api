#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/3 上午7:29
@Author : zsting29@gmail.com
@File   : jieba_service.py
"""
from dataclasses import dataclass

import jieba
from injector import inject
from jieba.analyse import default_tfidf

from internal.entity.jieba_entity import STOPWORD_SET


@inject
@dataclass
class JiebaService:
    """Jieba分詞服務"""

    def __init__(self):
        default_tfidf.stop_words = STOPWORD_SET

    @classmethod
    def extract_keywords(cls, text: str, max_keyword_pre_chunk: int = 10) -> list[str]:
        """根據輸入的文本，提取對應文本的關鍵詞列表"""
        return jieba.analyse.extract_tags(
            sentence=text,
            topK=max_keyword_pre_chunk
        )
