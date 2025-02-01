#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/31 下午3:55
@Author : zsting29@gmail.com
@File   : CallbackUse.py
"""
import time
from typing import Any, Optional, Union
from uuid import UUID

import dotenv
from langchain_core.callbacks import StdOutCallbackHandler, BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.outputs import GenerationChunk, ChatGenerationChunk, LLMResult
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


class LLMOpsCallbackHandler(BaseCallbackHandler):
    """自定義LLMOps回調處理器"""
    start_at: float = 0

    def on_chat_model_start(
            self,
            serialized: dict[str, Any],
            messages: list[list[BaseMessage]],
            *,
            run_id: UUID,
            parent_run_id: Optional[UUID] = None,
            tags: Optional[list[str]] = None,
            metadata: Optional[dict[str, Any]] = None,
            **kwargs: Any,
    ) -> Any:
        print("[Chat Model start...]")
        print("serialized: ", serialized)
        print("messages: ", messages)
        self.start_at = time.time()

    def on_llm_new_token(
            self,
            token: str,
            *,
            chunk: Optional[Union[GenerationChunk, ChatGenerationChunk]] = None,
            run_id: UUID,
            parent_run_id: Optional[UUID] = None,
            **kwargs: Any,
    ) -> Any:
        # print("[Token Generated...]")
        # print("token: ", token)
        # print("run_id: ", run_id)
        # print("parent_run_id: ", parent_run_id)
        pass

    def on_llm_end(
            self,
            response: LLMResult,
            *,
            run_id: UUID,
            parent_run_id: Optional[UUID] = None,
            **kwargs: Any,
    ) -> Any:
        end_at: float = time.time()
        print(f"流程消耗：{end_at - self.start_at}")
        print("response: ", response)


# 編排prompt
prompt = ChatPromptTemplate.from_template("{query}")
# 大語言模型
llm = ChatOpenAI(model="gpt-3.5-turbo-16k")
# 輸出解析器
parser = StrOutputParser()
# 編排鏈
chain = {"query": RunnablePassthrough()} | prompt | llm | parser
# 調用鏈 invoke -> stream
content = chain.stream(
    "你好，你是誰？",
    config={
        "callbacks": [
            StdOutCallbackHandler(),
            LLMOpsCallbackHandler()
        ]
    }
)
# print(content)

for chunk in content:
    pass
