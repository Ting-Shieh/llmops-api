#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/17 下午10:43
@Author : zsting29@gmail.com
@File   : RunBindTest.py
"""

from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from GoogleSearchTool2 import GoogleSerperArgsSchema
from WeatherTool import GoogleWeatherTool

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

# 1.創建prompt
prompt = ChatPromptTemplate.from_messages([
    ("human", [
        {"type": "text", "text": "請獲取下上傳圖片對應城市的天氣資訊。"},
        {"type": "image_url", "image_url": {"url": "{image_url}"}}
    ])
])
weather_prompt = ChatPromptTemplate.from_template("""請整理一下傳遞的城市的天氣預報資訊，並以用戶友好的方式輸出。

<weather>
{weather}
</weather>""")

# 2.創建大語言模型並綁定工具
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools=[GoogleWeatherTool()], tool_choice="google_weather")

# 3.創建鏈並執行工具
# chain = {"weather": ""} | weather_prompt | llm | StrOutputParser() # 基礎邏輯
sub_chain = (
        {"image_url": RunnablePassthrough()}
        | prompt
        | llm_with_tools
        | (lambda msg: msg.tool_calls[0]["args"])
        | GoogleWeatherTool()
)
chain = {"weather": sub_chain} | weather_prompt | llm | StrOutputParser()  # 基礎邏輯
print(chain.invoke("https://blog-static.kkday.com/zh-hk/blog/wp-content/uploads/batch_DSCF5739-1.jpg"))
