#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/29 下午1:46
@Author : zsting29@gmail.com
@File   : JsonOutputParser.py
"""
import dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic.v1 import BaseModel, Field

dotenv.load_dotenv()


# 1.create a json -> tell to LLM how the json looks like?
class Joke(BaseModel):
    joke: str = Field(description="回答用戶的冷笑話")
    punchline: str = Field(description="冷笑話的笑點")


parser = JsonOutputParser(pydantic_object=Joke)

# 2.create prompt template
prompt = ChatPromptTemplate.from_template("請依據用戶提問進行回答．\n{format_instructions}\n{query}").partial(
    format_instructions=parser.get_format_instructions())
# print(parser.get_format_instructions())
# print(prompt.format(query="請講一個過年的冷笑話"))

# 3.create LLM
llm = ChatOpenAI(model="gpt-4o")

# 4.transfer prompt and parser it
joke = parser.invoke(
    llm.invoke(
        prompt.invoke({"query": "請講一個過年的冷笑話"})
    )
)

print(joke)
print(type(joke))
