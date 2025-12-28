#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:49
@Author : zsting29@gmail.com
@File   : iteration_node.py
"""
import json
import logging
import time
from typing import Optional, Any

from internal.entity.workflow_entity import WorkflowStatus
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState, WorkflowConfig
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from internal.model import Workflow
from .iteration_entity import IterationNodeData


class IterationNode(BaseNode):
    """迭代節點"""
    node_data: IterationNodeData
    workflow: Any = None

    def __init__(self, *args: Any, **kwargs: Any):
        """構造函數，完成數據的初始化"""
        try:
            # 1.調用父類構造函數完成數據初始化
            super().__init__(*args, **kwargs)

            # 2.判斷是否傳遞的工作流id
            if len(self.node_data.workflow_ids) != 1:
                self.workflow = None
            else:
                # 3.導入依賴注入及相關服務
                from app.http.module import injector
                from pkg.sqlalchemy import SQLAlchemy

                db = injector.get(SQLAlchemy)
                workflow_record = db.session.query(Workflow).get(self.node_data.workflow_ids[0])

                # 4.判斷工作流是否存在並且已發布
                if not workflow_record or workflow_record.status != WorkflowStatus.PUBLISHED:
                    self.workflow = None
                else:
                    # 5.已發布且存在，則構建工作流並儲存
                    from internal.core.workflow import Workflow as WorkflowTool
                    self.workflow = WorkflowTool(
                        workflow_config=WorkflowConfig(
                            account_id=workflow_record.account_id,
                            name="iteration_workflow",
                            description=self.node_data.description,
                            nodes=workflow_record.graph.get("nodes", []),
                            edges=workflow_record.graph.get("edges", [])
                        ),
                    )
        except Exception as error:
            # 6.出現異常則將工作流重設為空，使用相對寬鬆的校驗範式
            logging.error("迭代節點子工作流構建失敗: %(error)s", {"error": error}, exc_info=True)
            self.workflow = None

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """迭代節點調用函數，循環遍歷將工作流的結果進行輸出"""
        # 1.提取節點輸入變數字典映射
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)
        inputs = inputs_dict.get("inputs", [])

        # 2.異常檢測，涵蓋工作流不存在、工作流輸入參數不唯一、數據為非列表、長度為0等
        if (
                self.workflow is None
                or len(self.workflow.args) != 1
                or not isinstance(inputs, list)
                or len(inputs) == 0
        ):
            return {
                "node_results": [
                    NodeResult(
                        node_data=self.node_data,
                        status=NodeStatus.FAILED,
                        inputs=inputs_dict,
                        outputs={"outputs": []},
                        latency=(time.perf_counter() - start_at),
                    )
                ]
            }

        # 3.獲取工作流的輸入欄位結構
        param_key = list(self.workflow.args.keys())[0]

        # 4.工作流+數據均存在，則循環遍歷輸入數據調用迭代工作流獲取結果
        outputs = []
        for item in inputs:
            # 5.構建輸入字典資訊
            data = {param_key: item}

            # 6.調用工作流獲取結果，這裡可以修改為並行執行提升效率，得到的結構轉換成字串
            iteration_result = self.workflow.invoke(data)
            outputs.append(json.dumps(iteration_result, ensure_ascii=False))

        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs={"outputs": outputs},
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
