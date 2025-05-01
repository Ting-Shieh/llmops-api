#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/27 上午9:26
@Author : zsting29@gmail.com
@File   : LangGraphStudy1.py
"""
import json
from typing import TypedDict, Annotated, Any, Literal

import dotenv
from langchain_community.tools import GoogleSerperRun
from langchain_community.tools.openai_dalle_image_generation import OpenAIDALLEImageGenerationTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import add_messages, StateGraph
from pydantic import BaseModel, Field

from study.CustomTools.WeatherTool import GoogleWeatherTool

dotenv.load_dotenv()

llm = ChatOpenAI(model="gpt-3.5-turbo")


# create 狀態圖，並使用作為狀態數據
class State(TypedDict):
    """圖結構的狀態數據"""
    messages: Annotated[list[BaseMessage], add_messages]
    use_name: str


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="執行Google Search 查詢語句")


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

dalle = OpenAIDALLEImageGenerationTool(api_wrapper=DallEAPIWrapper(model="dall-e-3"))

tools = [google_serper, dalle, google_weather]
llm_with_tools = llm.bind_tools(tools)


def chatbot_node(state: State, config: dict) -> Any:
    """聊天機器人節點，使用大語言模型根據傳遞的消息列表生成內容"""
    ai_message = llm.invoke(state["messages"])
    print("ai_message: ", ai_message)
    return {"messages": [ai_message], "use_name": "chatbot_node"}


def tool_executor(state: State, config: dict) -> Any:
    """工具執行節點"""
    # 1.構建工具名字映射字典
    tools_by_name = {tool.name: tool for tool in tools}
    # 2.提取最後一條消息裡的工具調用資訊
    tool_calls = state["messages"][-1].tool_calls
    # 3.循環遍歷執行工具
    messages = []
    for tool_call in tool_calls:
        # 4.獲取需要執行的工具
        tool = tools_by_name[tool_call["name"]]
        # 5.執行工具並將工具結果添加到消息列表中
        messages.append(ToolMessage(
            tool_call_id=tool_call["id"],
            content=json.dumps(tool.invoke(tool_call["args"])),
            name=tool_call["name"]
        ))
    # 6.返回更新的狀態資訊
    return {"messages": messages}


def route(state: State, config: dict) -> Literal["tool_executor", "__end__"]:
    """動態選擇工具執行亦或者結束節點"""
    # 1.獲取生成的最後一條消息
    ai_message = state["messages"][-1]
    # 2.檢測消息是否存在tool_calls參數，如果是則執行`工具路由`
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tool_executor"
    # 3.否則生成的內容是文本資訊，則跳轉到結束路由
    return END


graph_builder = StateGraph(State)

# add node
graph_builder.add_node("llm", chatbot_node)
graph_builder.add_node("tool_executor", tool_executor)

# add 邊(edge)
graph_builder.add_edge(START, "llm")
# graph_builder.add_conditional_edges("llm", route)
# graph_builder.add_edge("tool_executor", "llm")
graph_builder.add_edge("tool_executor", "llm")
graph_builder.add_conditional_edges("llm", route)  # 工具執行亦或者結束節點

# # 同上
# graph_builder.set_entry_point("llm")
# graph_builder.set_finish_point("llm")

# 編譯圖為Runnable
graph = graph_builder.compile()

# 調用
question1 = "2024年北京半程馬拉松的前3名成績是多少？"
question2 = "今天高雄天氣如何？"
state = graph.invoke({"messages": [("human", question2)]})
for message in state["messages"]:
    print("消息類型: ", message.type)
    if hasattr(message, "tool_calls") and len(message.tool_calls) > 0:
        print("工具調用參數: ", message.tool_calls)
    print("消息內容: ", message.content)
    print("=====================================")
