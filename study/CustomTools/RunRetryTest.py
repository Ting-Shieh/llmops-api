#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/17 下午10:43
@Author : zsting29@gmail.com
@File   : RunRetryTest.py
"""
from typing import Any

import dotenv
from langchain_core.messages import ToolCall, AIMessage, ToolMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


class CustomToolException(Exception):
    """自訂的工具錯誤異常"""

    def __init__(self, tool_call: ToolCall, exception: Exception) -> None:
        super().__init__()
        self.tool_call = tool_call
        self.exception = exception


@tool
def complex_tool(int_arg: int, float_arg: float, dict_arg: dict) -> int:
    """使用複雜工具進行複雜計算操作"""
    return int_arg * float_arg


def tool_custom_exception(msg: AIMessage, config: RunnableConfig) -> Any:
    try:
        return complex_tool.invoke(msg.tool_calls[0]["args"], config)
    except Exception as e:
        raise CustomToolException(msg.tool_calls[0], e)


def exception_to_messages(inputs: dict) -> dict:
    print("input:", inputs)
    # 1.從輸入中提取錯誤資訊
    exception = inputs.pop("exception")
    # 2.將歷史消息添加到原始輸入中，以便模型直到它在上一次工具調用中犯了一個錯誤
    messages = [
        AIMessage(content="", tool_calls=[exception.tool_call]),
        ToolMessage(tool_call_id=exception.tool_call["id"], content=str(exception.exception)),
        HumanMessage(content="最後一次工具調用引發了異常，請嘗試使用更正的參數再次調用該工具，不要重複犯錯。")
    ]
    inputs["last_output"] = messages
    return inputs


# 1.創建prompt，並預留占位符，用於儲存錯誤輸出資訊
prompt = ChatPromptTemplate.from_messages([
    ("human", "{query}"),
    ("placeholder", "{last_output}"),
])

# 2.創建大語言模型並綁定工具
llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools=[complex_tool])

# 3.創建鏈並執行工具
chain = prompt | llm | tool_custom_exception
self_correcting_chain = chain.with_fallbacks(
    [exception_to_messages | chain], exception_key="exception",
)

# 4.調用自我糾正鏈完成任務
print(self_correcting_chain.invoke({"query": "使用複雜工具，對應參數為5和2.1"}))
