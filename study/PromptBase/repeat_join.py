#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/19 下午2:55
@Author : zsting29@gmail.com
@File   : repeat_join.py
"""
from langchain_core.prompts import PromptTemplate, PipelinePromptTemplate

full_prompt = PromptTemplate.from_template("""{instruction}

{example}

{start}
""")

# 描述模板
instruction_prompt = PromptTemplate.from_template("你正在模擬{person}")

# 示例模板
example_prompt = PromptTemplate.from_template("""下面是一個交互式範例：
Q:{example_q}
A:{example_a}""")

# 開始模板
start_prompt = PromptTemplate.from_template("""現在，你是一個真實的人，請回答用戶問題：

Q:{input}
A:""")

pipeline_prompts = [
    ("instruction", instruction_prompt),
    ("example", example_prompt),
    ("start", start_prompt),
]
pipeline_prompt = PipelinePromptTemplate(
    final_prompt=full_prompt,
    pipeline_prompts=pipeline_prompts
)

print(pipeline_prompt)
print(pipeline_prompt.invoke({
    'input': "你最喜歡的運動品牌是什麼？",
    'person': "Ray",
    'example_a': "Tesla",
    'example_q': "你最喜歡的汽車品牌是什麼？"
}).to_string())
