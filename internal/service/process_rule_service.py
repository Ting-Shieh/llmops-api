#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/5 下午11:46
@Author : zsting29@gmail.com
@File   : process_rule_service.py
"""
import re
from dataclasses import dataclass
from typing import Callable

from injector import inject
from langchain_text_splitters import TextSplitter, RecursiveCharacterTextSplitter

from internal.model import ProcessRule


@inject
@dataclass
class ProcessRuleService:
    """處理規則服務"""

    @classmethod
    def get_text_splitter_by_process_rule(
            cls,
            process_rule: ProcessRule,
            length_function: Callable[[str], int] = len,
            **kwargs,
    ) -> TextSplitter:
        """根據傳遞的處理規則+長度計算函數，獲取相應的文本分割器"""
        return RecursiveCharacterTextSplitter(
            chunk_size=process_rule.rule["segment"]["chunk_size"],
            chunk_overlap=process_rule.rule["segment"]["chunk_overlap"],
            separators=process_rule.rule["segment"]["separators"],
            is_separator_regex=True,
            length_function=length_function,
            **kwargs
        )

    @classmethod
    def clean_text_by_process_rule(cls, text: str, process_rule: ProcessRule) -> str:
        """根據傳遞的處理規則清除多餘的字串"""
        # 1.循環遍歷所有預處理規則
        for pre_process_rule in process_rule.rule["pre_process_rules"]:
            # 2.刪除多餘空格
            if pre_process_rule["id"] == "remove_extra_space" and pre_process_rule["enabled"] is True:
                pattern = r'\n{3,}'
                text = re.sub(pattern, '\n\n', text)
                pattern = r'[\t\f\r\x20\u00a0\u1680\u180e\u2000-\u200a\u202f\u205f\u3000]{2,}'
                text = re.sub(pattern, ' ', text)
            # 3.刪除多餘的URL連結及信箱
            if pre_process_rule["id"] == "remove_url_and_email" and pre_process_rule["enabled"] is True:
                pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
                text = re.sub(pattern, '', text)
                pattern = r'https?://[^\s]+'
                text = re.sub(pattern, '', text)

        return text
