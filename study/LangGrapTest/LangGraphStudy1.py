#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/27 上午9:26
@Author : zsting29@gmail.com
@File   : LangGraphStudy1.py
"""
from typing import TypedDict, Annotated, Any

import dotenv
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import add_messages, StateGraph

dotenv.load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")


# create 狀態圖，並使用作為狀態數據
class State(TypedDict):
    """圖結構的狀態數據"""
    messages: Annotated[list[BaseMessage], add_messages]
    use_name: str


def chatbot_node(state: State, config: dict) -> Any:
    """聊天機器人節點，使用大語言模型根據傳遞的消息列表生成內容"""
    ai_message = llm.invoke(state["messages"])
    print("ai_message: ", ai_message)
    return {"messages": [ai_message], "use_name": "chatbot_node"}


graph_builder = StateGraph(State)

# add node
graph_builder.add_node("llm", chatbot_node)

# add 邊(edge)
graph_builder.add_edge(START, "llm")
graph_builder.add_edge("llm", END)
# # 同上
# graph_builder.set_entry_point("llm")
# graph_builder.set_finish_point("llm")

# 編譯圖為Runnable
graph = graph_builder.compile()

# 調用
print(graph.invoke({"messages": [("human", "告訴我特斯拉老闆是誰？")], "use_name": "graph"}))
