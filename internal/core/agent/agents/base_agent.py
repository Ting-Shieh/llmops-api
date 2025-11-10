#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/29 下午1:31
@Author : zsting29@gmail.com
@File   : base_agent.py
"""
import uuid
from abc import abstractmethod
from threading import Thread
from typing import Optional, Iterator, Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.load import Serializable
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from pydantic.v1 import PrivateAttr

from internal.core.agent.agents.agent_queue_manager import AgentQueueManager
from internal.core.agent.entities.agent_entity import AgentConfig, AgentState
from internal.core.agent.entities.queue_entity import QueueEvent, AgentResult, AgentThought
from internal.exception import FailException


class BaseAgent(Serializable, Runnable):
    """基於Runnable的基礎智慧體基類"""
    llm: BaseLanguageModel
    agent_config: AgentConfig
    _agent: CompiledStateGraph = PrivateAttr(None)
    _agent_queue_manager: AgentQueueManager = PrivateAttr(None)

    class Config:
        # 欄位允許接收任意類型，且不需要校驗器
        arbitrary_types_allowed = True

    def __init__(
            self,
            llm: BaseLanguageModel,
            agent_config: AgentConfig,
            *args,
            **kwargs,
    ):
        """構造函數，初始化智慧體圖結構程序"""
        super().__init__(*args, llm=llm, agent_config=agent_config, **kwargs)
        self._agent = self._build_agent()
        self._agent_queue_manager = AgentQueueManager(
            user_id=agent_config.user_id,
            invoke_from=agent_config.invoke_from,
        )

    @abstractmethod
    def _build_agent(self) -> CompiledStateGraph:
        """構建智慧體函數，等待子類實現"""
        raise NotImplementedError("_build_agent()未實現")

    def invoke(self, input: AgentState, config: Optional[RunnableConfig] = None) -> AgentResult:
        """塊內容響應，一次性生成完整內容後返回(開放API接口)"""
        # 1.調用stream方法獲取流式事件輸出數據
        content = input["messages"][0].content
        query = ""
        image_urls = []
        if isinstance(content, str):
            query = content
        elif isinstance(content, list):
            query = content[0]["text"]
            image_urls = [chunk["image_url"]["url"] for chunk in content if chunk.get("type") == "image_url"]
        agent_result = AgentResult(query=query, image_urls=image_urls)
        agent_thoughts = {}
        for agent_thought in self.stream(input, config):
            # 2.提取事件id並轉換成字串
            event_id = str(agent_thought.id)

            # 3.除了ping事件，其他事件全部記錄
            if agent_thought.event != QueueEvent.PING:
                # 4.單獨處理agent_message事件，因為該事件為數據疊加
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    # 5.檢測是否已儲存了事件
                    if event_id not in agent_thoughts:
                        # 6.初始化智慧體消息事件
                        agent_thoughts[event_id] = agent_thought
                    else:
                        # 7.疊加智慧體消息事件
                        agent_thoughts[event_id] = agent_thoughts[event_id].copy(update={
                            "thought": agent_thoughts[event_id].thought + agent_thought.thought,
                            "answer": agent_thoughts[event_id].answer + agent_thought.answer,
                            "latency": agent_thought.latency,
                        })
                    # 8.更新智慧體消息答案
                    agent_result.answer += agent_thought.answer
                else:
                    # 9.處理其他類型的智慧體事件，類型均為覆蓋
                    agent_thoughts[event_id] = agent_thought

                    # 10.單獨判斷是否為異常消息類型，如果是則修改狀態並記錄錯誤
                    if agent_thought.event in [QueueEvent.STOP, QueueEvent.TIMEOUT, QueueEvent.ERROR]:
                        agent_result.status = agent_thought.event
                        agent_result.error = agent_thought.observation if agent_thought.event == QueueEvent.ERROR else ""

        # 11.將推理字典轉換成列表並儲存
        agent_result.agent_thoughts = [agent_thought for agent_thought in agent_thoughts.values()]

        # 12.完善message
        agent_result.message = next(
            (agent_thought.message for agent_thought in agent_thoughts.values()
             if agent_thought.event == QueueEvent.AGENT_MESSAGE),
            []
        )

        # 13.更新總耗時
        agent_result.latency = sum([agent_thought.latency for agent_thought in agent_thoughts.values()])

        return agent_result

    def stream(
            self,
            input: AgentState,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[AgentThought]:
        """流式輸出，每個Not節點或者LLM每生成一個token時則會返回相應內容"""
        # 1.檢測子類是否已構建Agent智慧體，如果未構建則拋出錯誤
        if not self._agent:
            raise FailException("智慧體未成功構建，請核實後嘗試")

        # 2.構建對應的任務id及數據初始化
        input["task_id"] = input.get("task_id", uuid.uuid4())
        input["history"] = input.get("history", [])  # 沒有短期記憶
        input["iteration_count"] = input.get("iteration_count", 0)

        # 3.創建子執行緒並執行
        thread = Thread(
            target=self._agent.invoke,
            args=(input,)
        )
        thread.start()

        # 4.調用隊列管理器監聽數據並返回疊代器
        yield from self._agent_queue_manager.listen(input["task_id"])

    @property
    def agent_queue_manager(self) -> AgentQueueManager:
        """只讀屬性，返回智慧體隊列管理器"""
        return self._agent_queue_manager
