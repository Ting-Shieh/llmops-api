#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/31 下午1:42
@Author : zsting29@gmail.com
@File   : RunnableParallelMockSearch.py
"""
from operator import itemgetter

import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
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
# chain1 = prompt | llm | parser

# 調用鏈
# res = chain1.invoke({"context": retrieval("你好，我是誰？"), "query": "你好，我是誰？"})
# print(res)


# 編排鏈
# chain2 = RunnableParallel({
#     "context": lambda x: retrieval(x["query"]),
#     "query": itemgetter("query"),  # lambda x: x["query"],
# }) | prompt | llm | parser
chain2 = {
             "context": lambda x: retrieval(x["query"]),
             "query": itemgetter("query"),  # lambda x: x["query"],
         } | prompt | llm | parser

# 調用鏈
content = chain2.invoke({"query": "你好，我是誰？"})
print(content)
