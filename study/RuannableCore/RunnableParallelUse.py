#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/31 下午1:25
@Author : zsting29@gmail.com
@File   : RunnableParallelUse.py
"""
import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

# 編排prompt
joke_prompt = ChatPromptTemplate.from_template("請講一個關於{subject}的冷笑話，盡可能短一些")
poem_prompt = ChatPromptTemplate.from_template("請講一篇關於{subject}的詩，盡可能短一些")

# 大語言模型
llm = ChatOpenAI(model="gpt-3.5-turbo-16k")

# 輸出解析器
parser = StrOutputParser()

# 編排鏈
joke_chain = joke_prompt | llm | parser
poem_chain = poem_prompt | llm | parser

# 同時執行多條鏈
# map_chain = RunnableParallel(joke=joke_chain, poem=poem_chain)
map_chain = RunnableParallel({"joke": joke_chain, "poem": poem_chain})

res = map_chain.invoke(({"subject": "過年"}))

print(res)
