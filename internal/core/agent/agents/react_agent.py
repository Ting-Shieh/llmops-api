#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/1 下午7:21
@Author : zsting29@gmail.com
@File   : react_agent.py
"""
import json
import logging
import re
import time
import uuid

from langchain_core.messages import HumanMessage, RemoveMessage, messages_to_dict, SystemMessage, AIMessage
from langchain_core.tools import render_text_description_and_args

from internal.core.agent.entities.agent_entity import (
    REACT_AGENT_SYSTEM_PROMPT_TEMPLATE,
    AGENT_SYSTEM_PROMPT_TEMPLATE,
    AgentState, MAX_ITERATION_RESPONSE
)
from internal.core.agent.entities.queue_entity import QueueEvent, AgentThought
from internal.core.language_model.entities.model_entity import ModelFeature
from internal.exception import FailException
from .function_call_agent import FunctionCallAgent


class ReACTAgent(FunctionCallAgent):
    """基於ReACT推理的智慧體，繼承FunctionCallAgent，並重寫long_term_memory_node和llm_node兩個節點"""

    def _long_term_memory_recall_node(self, state: AgentState) -> AgentState:
        """重寫長期記憶召回節點，使用prompt實現工具調用及規範數據生成"""
        # 1.判斷是否支持工具調用，如果支持工具調用，則可以直接使用工具智慧體的長期記憶召回節點
        if ModelFeature.TOOL_CALL in self.llm.features:
            return super()._long_term_memory_recall_node(state)

        # 2.根據傳遞的智慧體配置判斷是否需要召回長期記憶
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.LONG_TERM_MEMORY_RECALL,
                observation=long_term_memory,
            ))

        # 3.檢測是否支持AGENT_THOUGHT，如果不支持，則使用沒有工具描述的prompt
        if ModelFeature.AGENT_THOUGHT not in self.llm.features:
            preset_messages = [
                SystemMessage(AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                    preset_prompt=self.agent_config.preset_prompt,
                    long_term_memory=long_term_memory,
                ))
            ]
        else:
            # 4.支持智慧體推理，則使用REACT_AGENT_SYSTEM_PROMPT_TEMPLATE並添加工具描述
            preset_messages = [
                SystemMessage(REACT_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                    preset_prompt=self.agent_config.preset_prompt,
                    long_term_memory=long_term_memory,
                    tool_description=render_text_description_and_args(self.agent_config.tools),
                ))
            ]

        # 5.將短期歷史消息添加到消息列表中
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            # 6.校驗歷史消息是不是複數形式，也就是[人類消息, AI消息, 人類消息, AI消息, ...]
            if len(history) % 2 != 0:
                self.agent_queue_manager.publish_error(state["task_id"], "智慧體歷史消息列表格式錯誤")
                logging.exception(
                    "智慧體歷史消息列表格式錯誤, len(history)=%(len_history)d, history=%(history)s",
                    {"len_history": len(history), "history": json.dumps(messages_to_dict(history))},
                )
                raise FailException("智慧體歷史消息列表格式錯誤")
            # 7.拼接歷史消息
            preset_messages.extend(history)

        # 8.拼接當前用戶的提問消息
        human_message = state["messages"][-1]
        preset_messages.append(HumanMessage(human_message.content))

        # 9.處理預設消息，將預設消息添加到用戶消息前，先去刪除用戶的原始消息，然後補充一個新的代替
        return {
            "messages": [
                RemoveMessage(id=human_message.id),
                *preset_messages
            ],
        }

    def _llm_node(self, state: AgentState) -> AgentState:
        """重寫工具調用智慧體的LLM節點"""
        # 1.判斷當前LLM是否支持tool_call，如果是則使用FunctionCallAgent的_llm_node
        if ModelFeature.TOOL_CALL in self.llm.features:
            return super()._llm_node(state)

        # 2.檢測當前Agent疊代次數是否符合需求
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
            return {
                "messages": [
                    AIMessage(MAX_ITERATION_RESPONSE)
                ]
            }

        # 3.從智慧體配置中提取大語言模型
        id = uuid.uuid4()
        start_at = time.perf_counter()
        llm = self.llm

        # 4.定義變數儲存流式輸出內容
        gathered = None
        is_first_chunk = True
        generation_type = ""

        # 5.流式輸出調用LLM，並判斷輸出內容是否以"```json"為開頭，用於區分工具調用和文本生成
        for chunk in llm.stream(state["messages"]):
            # 6.處理流式輸出內容塊疊加
            if is_first_chunk:
                gathered = chunk
                is_first_chunk = False
            else:
                gathered += chunk

            # 7.如果生成的是消息則提交智慧體消息事件
            if generation_type == "message":
                # 8.提取片段內容並校測是否開啟輸出審核
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

            # 9.檢測生成的類型是工具調用還是文本生成，同時賦值
            if not generation_type:
                # 10.當生成內容的長度大於等於7(```json)長度時才可以判斷出類型是什麼
                if len(gathered.content.strip()) >= 7:
                    if gathered.content.strip().startswith("```json"):
                        generation_type = "thought"
                    else:
                        generation_type = "message"
                        # 11.添加發布事件，避免前幾個字元遺漏
                        self.agent_queue_manager.publish(state["task_id"], AgentThought(
                            id=id,
                            task_id=state["task_id"],
                            event=QueueEvent.AGENT_MESSAGE,
                            thought=gathered.content,
                            message=messages_to_dict(state["messages"]),
                            answer=gathered.content,
                            latency=(time.perf_counter() - start_at),
                        ))

        # 8.計算LLM的輸入+輸出token總數
        input_token_count = self.llm.get_num_tokens_from_messages(state["messages"])
        output_token_count = self.llm.get_num_tokens_from_messages([gathered])

        # 9.獲取輸入/輸出價格和單位
        input_price, output_price, unit = self.llm.get_pricing()

        # 10.計算總token+總成本
        total_token_count = input_token_count + output_token_count
        total_price = (input_token_count * input_price + output_token_count * output_price) * unit

        # 12.如果類型為推理則解析json，並添加智慧體消息
        if generation_type == "thought":
            try:
                # 13.使用正則解析資訊，如果失敗則當成普通消息返回
                pattern = r"^```json(.*?)```$"
                matches = re.findall(pattern, gathered.content, re.DOTALL)
                match_json = json.loads(matches[0])
                tool_calls = [{
                    "id": str(uuid.uuid4()),
                    "type": "tool_call",
                    "name": match_json.get("name", ""),
                    "args": match_json.get("args", {}),
                }]
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=id,
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_THOUGHT,
                    thought=json.dumps(gathered.content),
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
                return {
                    "messages": [AIMessage(content="", tool_calls=tool_calls)],
                    "iteration_count": state["iteration_count"] + 1
                }
            except Exception as _:
                generation_type = "message"
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=id,
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=gathered.content,
                    message=messages_to_dict(state["messages"]),
                    answer=gathered.content,
                    latency=(time.perf_counter() - start_at),
                ))

        # 14.如果最終類型是message則表示已經拿到最終答案，則推送一條空內容並展示統計數據，同時停止監聽
        if generation_type == "message":
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

        return {"messages": [gathered], "iteration_count": state["iteration_count"] + 1}

    def _tools_node(self, state: AgentState) -> AgentState:
        """重寫工具節點，處理工具節點的`AI工具調用參數消息`與`工具消息轉人類消息`"""
        # 1.調用父類的工具節點執行並獲取結果
        super_agent_state = super()._tools_node(state)

        # 2.移除原始的AI工具調用參數消息，並創建新的ai消息
        tool_call_message = state["messages"][-1]
        remove_tool_call_message = RemoveMessage(id=tool_call_message.id)

        # 3.提取工具調用的第1條消息還原原始AI消息(ReACTAgent一次最多只有一個工具調用)
        tool_call_json = [{
            "name": tool_call_message.tool_calls[0].get("name", ""),
            "args": tool_call_message.tool_calls[0].get("args", {}),
        }]
        ai_message = AIMessage(content=f"```json\n{json.dumps(tool_call_json)}\n```")

        # 4.將ToolMessage轉換成HumanMessage，提升LLM的相容性
        tool_messages = super_agent_state["messages"]
        content = ""
        for tool_message in tool_messages:
            content += f"工具: {tool_message.name}\n執行結果: {tool_message.content}\n==========\n\n"
        human_message = HumanMessage(content=content)

        # 5.返回最終消息
        return {"messages": [remove_tool_call_message, ai_message, human_message]}
