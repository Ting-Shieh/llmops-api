#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/17 下午10:43
@Author : zsting29@gmail.com
@File   : RunBindTest.py
"""
from typing import TypedDict, Dict, Any, Optional

from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnablePassthrough
from langchain_core.tools import render_text_description_and_args
from langchain_openai import ChatOpenAI

from GoogleSearchTool2 import GoogleSerperArgsSchema
from WeatherTool import GoogleWeatherTool


class ToolCallRequest(TypedDict):
    name: str
    args: Dict[str, Any]


google_weather = GoogleWeatherTool()
google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "一个低成本的谷歌搜索API。"
        "当你需要回答有关时事的问题时，可以调用该工具。"
        "该工具的输入是搜索查询语句。"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)

tool_dict = {
    google_weather.name: google_weather,
    google_serper.name: google_serper
}
tools = [tool for tool in tool_dict.values()]


def invoke_tool(
        tool_call_request: ToolCallRequest,
        config: Optional[RunnableConfig] = None,
) -> str:
    """
    我們可以使用的執行工具調用的函數。
    :param tool_call_request:一個包含鍵名和參數的字典，名稱必須與現有工具的名稱匹配，參數是該工具的參數。
    :param config:這是LangChain使用的包含回調、元數據等資訊的配置資訊。
    :return:請求工具的輸出內容。
    """
    name = tool_call_request["name"]
    requested_tool = tool_dict.get(name)
    return requested_tool.invoke(tool_call_request.get("args"), config=config)


system_prompt = """是由OpenAI開發的聊天機器人，可訪問以下工具.
以下是每個工具的名稱和描述：

{rendered_tools}

根據用戶輸入，返回要使用的工具名稱和輸入.
將您的響應作為具有`name`和`args`鍵的Json塊返回.
`args`應該是一個字典，其中鍵對應於參數名稱，值對應於請求的值"""
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{query}")
]).partial(rendered_tools=render_text_description_and_args(tools))
# print(prompt.invoke({"query": "今天高雄天氣如何？"}).to_string())
# print('>>', render_text_description_and_args(tools))
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

# chain = prompt | llm | JsonOutputParser() | invoke_tool
chain = prompt | llm | JsonOutputParser() | RunnablePassthrough.assign(output=invoke_tool)
# print(chain.invoke({"query": "今天高雄天氣如何？"}))
print(chain.invoke({"query": "台積電現在股價多少？"}))
# # query = "今天高雄天氣如何？"
# query = "威剛科技股價歷史最高點為多少？"
# resp = chain.invoke(query)
# tool_calls = resp.tool_calls
# if len(tool_calls) <= 0:
#     print("Gen Content:", resp.content)
# else:
#     messages = prompt.invoke(query).to_messages()
#     messages.append(resp)
#
#     for tool_call in tool_calls:
#         tool = tool_dict.get(tool_call.get("name"))
#         print("now run tool name: ", tool.name)
#         result = tool.invoke(tool_call.get("args"))
#         print("tool result: ", result)
#         tool_call_id = tool_call.get("id")
#         messages.append(ToolMessage(
#             content=result,
#             tool_call_id=tool_call_id
#         ))
#     print("輸出內容:", llm_with_tools.invoke(messages))
