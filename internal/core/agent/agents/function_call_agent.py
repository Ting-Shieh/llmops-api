#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/30 下午7:11
@Author : zsting29@gmail.com
@File   : function_call_agent.py
"""
import json
import logging
import re
import time
import uuid
from typing import Literal

from langchain_core.messages import (
    messages_to_dict,
    AIMessage,
    SystemMessage,
    HumanMessage,
    RemoveMessage, ToolMessage
)
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.agents.base_agent import BaseAgent
from internal.core.agent.entities.agent_entity import (
    AgentState,
    AGENT_SYSTEM_PROMPT_TEMPLATE,
    MAX_ITERATION_RESPONSE, DATASET_RETRIEVAL_TOOL_NAME
)
from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.core.language_model.entities.model_entity import ModelFeature
from internal.exception import FailException


class FunctionCallAgent(BaseAgent):
    """基於函數/工具調用的智慧體"""

    def _build_agent(self) -> CompiledStateGraph:
        """構建LangGraph圖結構編譯程序"""
        # 1.創建圖
        graph = StateGraph(AgentState)

        # 2.添加節點
        graph.add_node("preset_operation", self._preset_operation_node)
        graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tools", self._tools_node)

        # 3.添加邊，並設置起點和終點
        graph.set_entry_point("preset_operation")
        graph.add_conditional_edges("preset_operation", self._preset_operation_condition)
        graph.add_edge("long_term_memory_recall", "llm")
        graph.add_conditional_edges("llm", self._tools_condition)
        graph.add_edge("tools", "llm")

        # 4.編譯應用並返回
        agent = graph.compile()

        return agent

    def _preset_operation_node(self, state: AgentState) -> AgentState:
        """預設操作，涵蓋：輸入審核、數據預處理、條件邊等"""
        # 1.獲取審核配置與用戶輸入query
        review_config = self.agent_config.review_config
        query = state["messages"][-1].content

        # 2.檢測是否開啟審核配置
        if review_config["enable"] and review_config["inputs_config"]["enable"]:
            contains_keyword = any(keyword in query for keyword in review_config["keywords"])
            # 3.如果包含敏感詞則執行後續步驟
            if contains_keyword:
                preset_response = review_config["inputs_config"]["preset_response"]
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=preset_response,
                    message=messages_to_dict(state["messages"]),
                    answer=preset_response,
                    latency=0,
                ))
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_END,
                ))
                return {"messages": [AIMessage(preset_response)]}

        return {"messages": []}

    def _long_term_memory_recall_node(self, state: AgentState) -> AgentState:
        """長期記憶召回節點"""
        # 1.根據傳遞的智慧體配置判斷是否需要召回長期記憶
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.LONG_TERM_MEMORY_RECALL,
                observation=long_term_memory,
            ))

        # 2.構建預設消息列表，並將preset_prompt+long_term_memory填充到系統消息中
        preset_messages = [
            SystemMessage(AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                preset_prompt=self.agent_config.preset_prompt,
                long_term_memory=long_term_memory,
            ))
        ]

        # 3.將短期歷史消息添加到消息列表中
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            # 4.校驗歷史消息是不是複數形式，也就是[人類消息, AI消息, 人類消息, AI消息, ...]
            if len(history) % 2 != 0:
                self.agent_queue_manager.publish_error(state["task_id"], "智慧體歷史消息列表格式錯誤")
                logging.exception(
                    "智慧體歷史消息列表格式錯誤, len(history)=%(len_history)d, history=%(history)s",
                    {"len_history": len(history), "history": json.dumps(messages_to_dict(history))},
                )
                raise FailException("智慧體歷史消息列表格式錯誤")
            # 5.拼接歷史消息
            preset_messages.extend(history)

        # 6.拼接當前用戶的提問資訊
        human_message = state["messages"][-1]
        preset_messages.append(HumanMessage(human_message.content))

        # 7.處理預設消息，將預設消息添加到用戶消息前，先去刪除用戶的原始消息，然後補充一個新的代替
        return {
            "messages": [RemoveMessage(id=human_message.id), *preset_messages],
        }

    def _llm_node(self, state: AgentState) -> AgentState:
        """大語言模型節點"""
        # 1.檢測當前Agent疊代次數是否符合需求
        if state["iteration_count"] > self.agent_config.max_iteration_count:
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=MAX_ITERATION_RESPONSE,
                    message=messages_to_dict(state["messages"]),
                    answer=MAX_ITERATION_RESPONSE,
                    latency=0,
                ))
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_END,
                ))
            return {"messages": [AIMessage(MAX_ITERATION_RESPONSE)]}

        # 2.從智慧體配置中提取大語言模型
        id = uuid.uuid4()
        start_at = time.perf_counter()
        llm = self.llm

        # 3.檢測大語言模型實例是否有bind_tools方法，如果沒有則不綁定，如果有還需要檢測tools是否為空，不為空則綁定
        if (
                ModelFeature.TOOL_CALL in llm.features
                and hasattr(llm, "bind_tools")
                and callable(getattr(llm, "bind_tools"))
                and len(self.agent_config.tools) > 0
        ):
            llm = llm.bind_tools(self.agent_config.tools)

        # 4.流式調用LLM輸出對應內容
        gathered = None
        is_first_chunk = True
        generation_type = ""
        try:
            for chunk in llm.stream(state["messages"]):
                if is_first_chunk:
                    gathered = chunk
                    is_first_chunk = False
                else:
                    gathered += chunk

                # 5.檢測生成類型是工具參數還是文本生成
                if not generation_type:
                    if chunk.tool_calls:
                        generation_type = "thought"
                    elif chunk.content:
                        generation_type = "message"

                # 6.如果生成的是消息則提交智慧體消息事件
                if generation_type == "message":
                    # 7.提取片段內容並檢測是否開啟輸出審核
                    review_config = self.agent_config.review_config
                    content = chunk.content
                    if review_config["enable"] and review_config["outputs_config"]["enable"]:
                        for keyword in review_config["keywords"]:
                            content = re.sub(re.escape(keyword), "**", content, flags=re.IGNORECASE)

                    self.agent_queue_manager.publish(state["task_id"], AgentThought(
                        id=id,
                        task_id=state["task_id"],
                        event=QueueEvent.AGENT_MESSAGE,
                        thought=content,
                        message=messages_to_dict(state["messages"]),
                        answer=content,
                        latency=(time.perf_counter() - start_at),
                    ))
        except Exception as e:
            logging.exception(
                "LLM節點發生錯誤, 錯誤資訊: %(error)s",
                {"error": str(e) or "LLM出現未知錯誤"}
            )
            self.agent_queue_manager.publish_error(
                state["task_id"],
                f"LLM節點發生錯誤, 錯誤資訊: {str(e) or 'LLM出現未知錯誤'}",
            )
            raise e

        # 8.計算LLM的輸入+輸出token總數
        input_token_count = self.llm.get_num_tokens_from_messages(state["messages"])
        output_token_count = self.llm.get_num_tokens_from_messages([gathered])

        # 9.獲取輸入/輸出價格和單位
        input_price, output_price, unit = self.llm.get_pricing()

        # 10.計算總token+總成本
        total_token_count = input_token_count + output_token_count
        total_price = (input_token_count * input_price + output_token_count * output_price) * unit

        # 11.如果類型為推理則添加智慧體推理事件
        if generation_type == "thought":
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=id,
                task_id=state["task_id"],
                event=QueueEvent.AGENT_THOUGHT,
                thought=json.dumps(gathered.tool_calls),
                # 消息相關欄位
                message=messages_to_dict(state["messages"]),
                message_token_count=input_token_count,
                message_unit_price=input_price,
                message_price_unit=unit,
                # 答案相關欄位
                answer="",
                answer_token_count=output_token_count,
                answer_unit_price=output_price,
                answer_price_unit=unit,
                # Agent推理統計相關
                total_token_count=total_token_count,
                total_price=total_price,
                latency=(time.perf_counter() - start_at),
            ))
        elif generation_type == "message":
            # 7.如果LLM直接生成answer則表示已經拿到了最終答案，推送一條空內容用於計算總token+總成本，並停止監聽
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=id,
                task_id=state["task_id"],
                event=QueueEvent.AGENT_MESSAGE,
                thought="",
                # 消息相關欄位
                message=messages_to_dict(state["messages"]),
                message_token_count=input_token_count,
                message_unit_price=input_price,
                message_price_unit=unit,
                # 答案相關欄位
                answer="",
                answer_token_count=output_token_count,
                answer_unit_price=output_price,
                answer_price_unit=unit,
                # Agent推理統計相關
                total_token_count=total_token_count,
                total_price=total_price,
                latency=(time.perf_counter() - start_at),
            ))
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.AGENT_END,
            ))

        return {
            "messages": [gathered],
            "iteration_count": state["iteration_count"] + 1
        }

    def _tools_node(self, state: AgentState) -> AgentState:
        """工具執行節點"""
        # 1.將工具列錶轉換成字典，便於調用指定的工具
        tools_by_name = {tool.name: tool for tool in self.agent_config.tools}

        # 2.提取消息中的工具調用參數
        tool_calls = state["messages"][-1].tool_calls

        # 3.循環執行工具組裝工具消息
        messages = []
        for tool_call in tool_calls:
            # 4.創建智慧體動作事件id並記錄開始時間
            id = uuid.uuid4()
            start_at = time.perf_counter()

            try:
                # 5.獲取工具並調用工具
                tool = tools_by_name[tool_call["name"]]
                tool_result = tool.invoke(tool_call["args"])
            except Exception as e:
                # 6.添加錯誤工具資訊
                tool_result = f"工具执行出错: {str(e)}"

            # 7.將工具消息添加到消息列表中
            messages.append(ToolMessage(
                tool_call_id=tool_call["id"],
                content=json.dumps(tool_result),
                name=tool_call["name"],
            ))

            # 7.判斷執行工具的名字，提交不同事件，涵蓋智慧體動作以及知識庫檢索
            event = (
                QueueEvent.AGENT_ACTION
                if tool_call["name"] != DATASET_RETRIEVAL_TOOL_NAME
                else QueueEvent.DATASET_RETRIEVAL
            )
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=id,
                task_id=state["task_id"],
                event=event,
                observation=json.dumps(tool_result),
                tool=tool_call["name"],
                tool_input=tool_call["args"],
                latency=(time.perf_counter() - start_at),
            ))

        return {"messages": messages}

    @classmethod
    def _tools_condition(cls, state: AgentState) -> Literal["tools", "__end__"]:
        """檢測下一個節點是執行tools節點，還是直接結束"""
        # 1.提取狀態中的最後一條消息(AI消息)
        messages = state["messages"]
        ai_message = messages[-1]

        # 2.檢測是否存在tools_calls這個參數，如果存在則執行tools節點，否則結束
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"

        return END

    @classmethod
    def _preset_operation_condition(cls, state: AgentState) -> Literal["long_term_memory_recall", "__end__"]:
        """預設操作條件邊，用於判斷是否觸發預設響應"""
        # 1.提取狀態的最後一條消息
        message = state["messages"][-1]

        # 2.判斷消息的類型，如果是AI消息則說明觸發了審核機制，直接結束
        if message.type == "ai":
            return END

        return "long_term_memory_recall"
