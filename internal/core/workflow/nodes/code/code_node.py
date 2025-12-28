#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:29
@Author : zsting29@gmail.com
@File   : code_node.py
"""
import ast
import time
from typing import Optional

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.variable_entity import VARIABLE_TYPE_DEFAULT_VALUE_MAP
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from internal.exception import FailException
from .code_entity import CodeNodeData


class CodeNode(BaseNode):
    """Python代碼運行節點"""
    node_data: CodeNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """Python代碼運行節點，執行的代碼函數名字必須為main，並且參數名為params，有且只有一個參數，不允許有額外的其他語句"""
        # 1.從狀態中提取輸入數據
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # todo:2.執行Python代碼，該方法目前可以執行任意的Python代碼，所以非常危險，後期需要單獨將這部分功能遷移到沙盒中或者指定容器中運行和項目分離
        result = self._execute_function(self.node_data.code, params=inputs_dict)

        # 3.檢測函數的返回值是否為字典
        if not isinstance(result, dict):
            raise FailException("main函數的返回值必須是一個字典")

        # 4.提取輸出數據
        outputs_dict = {}
        outputs = self.node_data.outputs
        for output in outputs:
            # 5.提取輸出數據(非嚴格校驗)
            outputs_dict[output.name] = result.get(
                output.name,
                VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(output.type),
            )

        # 6.構建狀態數據並返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs_dict,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }

    @classmethod
    def _execute_function(cls, code: str, *args, **kwargs):
        """執行Python函數代碼"""
        try:
            # 1.解析代碼為AST(抽象語法樹)
            tree = ast.parse(code)

            # 2.定義變數用於檢查是否找到main函數
            main_func = None

            # 3.循環遍歷語法樹
            for node in tree.body:
                # 4.判斷節點類型是否為函數
                if isinstance(node, ast.FunctionDef):
                    # 5.檢查函數名稱是否為main
                    if node.name == "main":
                        if main_func:
                            raise FailException("代碼中只能有一個main函數")

                        # 6.檢測main函數的參數是否為params，如果不是則拋出錯誤
                        if len(node.args.args) != 1 or node.args.args[0].arg != "params":
                            raise FailException("main函數必須只有一個參數，且參數為params")

                        main_func = node
                    else:
                        # 7.其他函數的情況，直接拋出錯誤
                        raise FailException("代碼中不能包含其他函數，只能有main函數")
                else:
                    # 8.非函數的情況，直接拋出錯誤
                    raise FailException("代碼中只能包含函數定義，不允許其他語句存在")

            # 9.判斷下是否找到main函數
            if not main_func:
                raise FailException("代碼中必須包含名為main的函數")

            # 10.代碼通過AST校驗，執行程式碼
            local_vars = {}
            exec(code, {}, local_vars)

            # 11.調用並執行main函數
            if "main" in local_vars and callable(local_vars["main"]):
                return local_vars["main"](*args, **kwargs)
            else:
                raise FailException("main函數必須是一個可調用的函數")
        except Exception as e:
            raise FailException("Python代碼執行出錯")
