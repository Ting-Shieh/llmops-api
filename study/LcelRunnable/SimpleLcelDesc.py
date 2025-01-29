#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/29 下午3:52
@Author : zsting29@gmail.com
@File   : SimpleLcelDesc.py
"""

import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

prompt = ChatPromptTemplate.from_template("{query}")
llm = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

# create a chain
chain = prompt | llm | parser

# call chain and get result
print(chain.invoke({"query": "告訴我特斯拉老闆是誰？"}))
