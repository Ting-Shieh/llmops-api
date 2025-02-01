#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/31 下午2:33
@Author : zsting29@gmail.com
@File   : RunnablePassthrough.py
"""

import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


def retrieval(query: str) -> str:
    """模擬檢索器函數"""
    print(f"正在檢索:{query}")
    return "我是Ting"


# 編排prompt
prompt = ChatPromptTemplate.from_template(
    """請根據用戶問題回答，可以根據對應上下文進行生成．
    <context>
    {context}
    </context>
    用戶的提問是:{query}
    """
)

# 大語言模型
llm = ChatOpenAI(model="gpt-3.5-turbo-16k")

# 輸出解析器
parser = StrOutputParser()

# 編排鏈
chain = RunnablePassthrough.assign(context=lambda x: retrieval(x["query"])) | prompt | llm | parser

# 調用鏈
content = chain.invoke({"query": "你好，我是誰？"})
print(content)
