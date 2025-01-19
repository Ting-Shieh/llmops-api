#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/19 下午2:35
@Author : zsting29@gmail.com
@File   : string_join.py
"""
from langchain_core.prompts import PromptTemplate

prompt = (
        PromptTemplate.from_template("請講一個關於{subject}的冷笑話")
        + ", 讓我開心一下 \n"
        + "使用{language}語言"
)
prompt_value = prompt.invoke({"subject": "工程師", "language": "英文"})
print(prompt)
print(prompt_value.to_string())
