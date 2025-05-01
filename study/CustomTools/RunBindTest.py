#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/17 下午10:43
@Author : zsting29@gmail.com
@File   : RunBindTest.py
"""

from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from GoogleSearchTool2 import GoogleSerperArgsSchema
from WeatherTool import GoogleWeatherTool

google_weather = GoogleWeatherTool()
google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "一個低成本的Google搜索API。"
        "當你需要回答有關時事的問題時，可以調用該工具。"
        "該工具的輸入是搜索查詢語句。"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)

tool_dict = {
    google_weather.name: google_weather,
    google_serper.name: google_serper
}
tools = [tool for tool in tool_dict.values()]

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是由OpenAId開發的聊天機器人，可幫助用戶回答問題，必要時刻請調用工具幫助用戶解答"),
    ("human", "{query}")
])
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

llm_with_tools = llm.bind_tools(tools=tools)

chain = {"query": RunnablePassthrough()} | prompt | llm_with_tools

query = "今天高雄天氣如何？"
# query = "威剛科技股價歷史最高點為多少？"
resp = chain.invoke(query)
tool_calls = resp.tool_calls
if len(tool_calls) <= 0:
    print("Gen Content:", resp.content)
else:
    messages = prompt.invoke(query).to_messages()
    messages.append(resp)

    for tool_call in tool_calls:
        tool = tool_dict.get(tool_call.get("name"))
        print("now run tool name: ", tool.name)
        result = tool.invoke(tool_call.get("args"))
        print("tool result: ", result)
        tool_call_id = tool_call.get("id")
        messages.append(ToolMessage(
            content=result,
            tool_call_id=tool_call_id
        ))
    print("輸出內容:", llm_with_tools.invoke(messages))
