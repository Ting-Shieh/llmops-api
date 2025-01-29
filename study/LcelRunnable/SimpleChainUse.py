#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/29 下午3:39
@Author : zsting29@gmail.com
@File   : SimpleChainUse.py
"""
from typing import Any

import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

prompt = ChatPromptTemplate.from_template("{query}")
llm = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()


# define a Chain
class Chain:
    steps: list = []

    def __init__(self, steps: list):
        self.steps = steps

    def invoke(self, input: Any):
        for step in self.steps:
            input = step.invoke(input)
            print("step: ", step)
            print("output: ", input)
            print("============")
        return input


# arrange Chain
chain = Chain([prompt, llm, parser])
print(chain.invoke({"query": "告訴我特斯拉老闆是誰？"}))
