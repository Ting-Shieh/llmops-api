#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/19 下午2:55
@Author : zsting29@gmail.com
@File   : repeat_join.py
"""
from langchain.prompts import PromptTemplate

# 定義模板內容
prompt_templates = {
    "instruction": "你正在模擬{person}",
    "example": """下面是一個交互式範例：
Q:{example_q}
A:{example_a}""",
    "start": """現在，你是一個真實的人，請回答用戶問題：

Q:{input}
A:"""
}

# 創建 pipeline_prompts
pipeline_prompts = [(key, PromptTemplate.from_template(template)) for key, template in prompt_templates.items()]

# 定義輸入參數
my_input = {
    "person": "AI 助手",
    "example_q": "這是什麼？",
    "example_a": "這是一個範例。",
    "input": "請問今天的天氣怎麼樣？"
}

# 遍歷 pipeline_prompts 並生成輸出
for name, prompt in pipeline_prompts:
    my_input[name] = prompt.invoke(my_input).to_string()

# 最終組合輸出
final_prompt = PromptTemplate.from_template("""
{instruction}

{example}

{start}
""")
my_output = final_prompt.invoke(my_input).to_string()

# 輸出結果
print(my_output)
