#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/15 下午11:28
@Author : zsting29@gmail.com
@File   : agent_queue_manager.py
"""
import queue
import time
import uuid
from queue import Queue
from typing import Generator
from uuid import UUID

from redis import Redis

from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.entity.conversation_entity import InvokeFrom


class AgentQueueManager:
    """智慧體隊列管理器"""
    redis_client: Redis
    invoke_from: InvokeFrom
    user_id: UUID
    _queues: dict[str, Queue]

    def __init__(
            self,
            user_id: UUID,
            invoke_from: InvokeFrom,
    ) -> None:
        """構造函數，初始化智慧體隊列管理器"""
        # 1.初始化數據
        self.user_id = user_id
        self.invoke_from = invoke_from
        self._queues = {}

        # 2.內部初始化redis_client
        from app.http.module import injector
        self.redis_client = injector.get(Redis)

    def listen(self, task_id: UUID) -> Generator:
        """監聽隊列返回的生成式數據"""
        # 1.定義基礎數據記錄超時時間、開始時間、最後一次ping通時間
        listen_timeout = 600
        start_time = time.time()
        last_ping_time = 0

        # 2.創建循環隊列執行死循環讀取數據，直到超時或者數據讀取完畢
        while True:
            try:
                # 3.從隊列中提取數據並檢測數據是否存在，如果存在則使用yield關鍵字返回
                item = self.queue(task_id).get(timeout=1)
                if item is None:
                    break
                yield item
            except queue.Empty:
                continue
            finally:
                # 4.計算獲取數據的總耗時
                elapsed_time = time.time() - start_time

                # 5.每10秒發起一個ping請求
                if elapsed_time // 10 > last_ping_time:
                    self.publish(task_id, AgentThought(
                        id=uuid.uuid4(),
                        task_id=task_id,
                        event=QueueEvent.PING,
                    ))
                    last_ping_time = elapsed_time // 10

                # 6.判斷總耗時是否超時，如果超時則往隊列中添加超時事件
                if elapsed_time >= listen_timeout:
                    self.publish(task_id, AgentThought(
                        id=uuid.uuid4(),
                        task_id=task_id,
                        event=QueueEvent.TIMEOUT,
                    ))

                # 7.檢測是否停止，如果已經停止則添加停止事件
                if self._is_stopped(task_id):
                    self.publish(task_id, AgentThought(
                        id=uuid.uuid4(),
                        task_id=task_id,
                        event=QueueEvent.STOP,
                    ))

    def stop_listen(self, task_id: UUID) -> None:
        """停止監聽隊列資訊"""
        self.queue(task_id).put(None)

    def publish(self, task_id: UUID, agent_thought: AgentThought) -> None:
        """發布事件資訊到隊列"""
        # 1.將事件添加到隊列中
        self.queue(task_id).put(agent_thought)

        # 2.檢測事件類型是否為需要停止的類型，涵蓋STOP、ERROR、TIMEOUT、AGENT_END
        need_stop_type_list = [QueueEvent.STOP, QueueEvent.ERROR, QueueEvent.TIMEOUT,
                               QueueEvent.AGENT_END]
        if agent_thought.event in need_stop_type_list:
            self.stop_listen(task_id)

    def publish_error(self, task_id: UUID, error) -> None:
        """發布錯誤資訊到隊列"""
        self.publish(task_id, AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.ERROR,
            observation=str(error),
        ))

    def _is_stopped(self, task_id: UUID) -> bool:
        """檢測任務是否停止"""
        task_stopped_cache_key = self.generate_task_stopped_cache_key(task_id)
        result = self.redis_client.get(task_stopped_cache_key)

        if result is not None:
            return True
        return False

    def queue(self, task_id: UUID) -> Queue:
        """根據傳遞的task_id獲取對應的任務隊列資訊"""
        # 1.從隊列字典中獲取對應的任務隊列
        q = self._queues.get(str(task_id))

        # 2.檢測隊列是否存在，如果不存在則創建隊列，並添加快取鍵標識
        if not q:
            # 3.添加快取鍵標識
            user_prefix = "account" if self.invoke_from in [
                InvokeFrom.WEB_APP,
                InvokeFrom.DEBUGGER,
                InvokeFrom.ASSISTANT_AGENT,
            ] else "end-user"

            # 4.設置任務對應的快取鍵，代表這次任務已經開始了
            self.redis_client.setex(
                self.generate_task_belong_cache_key(task_id),
                1800,
                f"{user_prefix}-{str(self.user_id)}",
            )

            # 5.將任務隊列添加到隊列字典中
            q = Queue()
            self._queues[str(task_id)] = q

        return q

    @classmethod
    def set_stop_flag(cls, task_id: UUID, invoke_from: InvokeFrom, user_id: UUID) -> None:
        """根據傳遞的任務id+調用來源停止某次會話"""
        # 1.獲取redis_client用戶端
        from app.http.module import injector
        redis_client = injector.get(Redis)

        # 2.獲取當前任務的快取鍵，如果任務沒執行，則不需要停止
        result = redis_client.get(cls.generate_task_belong_cache_key(task_id))
        if not result:
            return

        # 3.計算對應快取鍵的結果
        user_prefix = "account" if invoke_from in [
            InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER, InvokeFrom.ASSISTANT_AGENT,
        ] else "end-user"
        if result.decode("utf-8") != f"{user_prefix}-{str(user_id)}":
            return

        # 4.生成停止鍵標識
        stopped_cache_key = cls.generate_task_stopped_cache_key(task_id)
        redis_client.setex(stopped_cache_key, 600, 1)

    @classmethod
    def generate_task_belong_cache_key(cls, task_id: UUID) -> str:
        """生成任務專屬的快取鍵"""
        return f"generate_task_belong:{str(task_id)}"

    @classmethod
    def generate_task_stopped_cache_key(cls, task_id: UUID) -> str:
        """生成任務已停止的快取鍵"""
        return f"generate_task_stopped:{str(task_id)}"
