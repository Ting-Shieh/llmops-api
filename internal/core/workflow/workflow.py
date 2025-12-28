#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:19
@Author : zsting29@gmail.com
@File   : workflow.py
"""
from typing import Any, Optional, Iterator

from flask import current_app
from langchain_core.pydantic_v1 import PrivateAttr, BaseModel, Field, create_model
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph, StateGraph

from internal.core.workflow.entities.node_entity import NodeType
from internal.core.workflow.entities.variable_entity import VARIABLE_TYPE_MAP
from internal.core.workflow.entities.workflow_entity import WorkflowConfig, WorkflowState
from internal.core.workflow.nodes import EndNode, StartNode, LLMNode, CodeNode, TemplateTransformNode, \
    DatasetRetrievalNode, ToolNode, HttpRequestNode, QuestionClassifierNode, IterationNode, QuestionClassifierNodeData
from internal.exception import ValidateErrorException

# 節點類映射
NodeClasses = {
    NodeType.START: StartNode,
    NodeType.END: EndNode,
    NodeType.LLM: LLMNode,
    NodeType.TEMPLATE_TRANSFORM: TemplateTransformNode,
    NodeType.DATASET_RETRIEVAL: DatasetRetrievalNode,
    NodeType.CODE: CodeNode,
    NodeType.TOOL: ToolNode,
    NodeType.HTTP_REQUEST: HttpRequestNode,
    NodeType.QUESTION_CLASSIFIER: QuestionClassifierNode,
    NodeType.ITERATION: IterationNode,
}


class Workflow(BaseTool):
    """工作流LangChain工具類"""
    _workflow_config: WorkflowConfig = PrivateAttr(None)
    _workflow: CompiledStateGraph = PrivateAttr(None)

    def __init__(self, workflow_config: WorkflowConfig, **kwargs: Any):
        """構造函數，完成工作流函數的初始化"""
        # 1.調用父類構造函數完成基礎數據初始化
        super().__init__(
            name=workflow_config.name,
            description=workflow_config.description,
            args_schema=self._build_args_schema(workflow_config),
            **kwargs
        )

        # 2.完善工作流配置與工作流圖結構程序的初始化
        self._workflow_config = workflow_config
        self._workflow = self._build_workflow()

    @classmethod
    def _build_args_schema(cls, workflow_config: WorkflowConfig) -> type[BaseModel]:
        """構建輸入參數結構體"""
        # 1.提取開始節點的輸入參數資訊
        fields = {}
        inputs = next(
            (node.inputs for node in workflow_config.nodes if node.node_type == NodeType.START),
            []
        )

        # 2.循環遍歷所有輸入資訊並創建欄位映射
        for input in inputs:
            field_name = input.name
            field_type = VARIABLE_TYPE_MAP.get(input.type, str)
            field_required = input.required
            field_description = input.description

            fields[field_name] = (
                field_type if field_required else Optional[field_type],
                Field(description=field_description),
            )

        # 3.調用create_model創建一個BaseModel類，並使用上述分析好的欄位
        return create_model("DynamicModel", **fields)

    def _build_workflow(self) -> CompiledStateGraph:
        """構建編譯後的工作流圖程序"""
        # 1.創建graph圖程序結構
        graph = StateGraph(WorkflowState)

        # 2.提取nodes和edges資訊
        nodes = self._workflow_config.nodes
        edges = self._workflow_config.edges

        # 3.循環遍歷nodes節點資訊添加節點
        for node in nodes:
            node_flag = f"{node.node_type.value}_{node.id}"
            if node.node_type == NodeType.START:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.START](node_data=node),
                )
            elif node.node_type == NodeType.LLM:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.LLM](node_data=node),
                )
            elif node.node_type == NodeType.TEMPLATE_TRANSFORM:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.TEMPLATE_TRANSFORM](node_data=node),
                )
            elif node.node_type == NodeType.DATASET_RETRIEVAL:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.DATASET_RETRIEVAL](
                        flask_app=current_app._get_current_object(),
                        account_id=self._workflow_config.account_id,
                        node_data=node,
                    ),
                )
            elif node.node_type == NodeType.CODE:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.CODE](node_data=node),
                )
            elif node.node_type == NodeType.TOOL:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.TOOL](node_data=node),
                )
            elif node.node_type == NodeType.HTTP_REQUEST:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.HTTP_REQUEST](node_data=node),
                )
            elif node.node_type == NodeType.END:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.END](node_data=node),
                )
            elif node.node_type == NodeType.QUESTION_CLASSIFIER:
                # 4.問題分類節點為條件邊對應的節點，可以添加一個虛擬起始節點並返回空字典什麼都不處理，讓條件邊可以快速找到起點
                graph.add_node(
                    node_flag,
                    lambda state: {"node_results": []}
                )

                # 4.1[補充更新] 同步獲取意圖識別節點的數據，添加虛擬終止節點(每個分類一個節點)並返回空字典什麼都不處理，讓意圖節點實現並行運行
                assert isinstance(node, QuestionClassifierNodeData)
                for item in node.classes:
                    graph.add_node(
                        f"qc_source_handle_{str(item.source_handle_id)}",
                        lambda state: {"node_results": []}
                    )

                # 4.2[補充更新] 將虛擬起點和終點使用條件邊進行拼接
                graph.add_conditional_edges(
                    node_flag,
                    NodeClasses[NodeType.QUESTION_CLASSIFIER](node_data=node)
                )
            elif node.node_type == NodeType.ITERATION:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.ITERATION](node_data=node)
                )
            else:
                raise ValidateErrorException("工作流節點類型錯誤，請核實後重試")

        # 5.循環遍歷edges資訊添加邊
        parallel_edges = {}  # key:終點，value:起點列表
        start_node = ""
        end_node = ""
        non_parallel_nodes = []  # 用於儲存不能並行執行的節點列表資訊(主要用來處理意圖節點的虛擬起點和終點)
        for edge in edges:
            # 6.計算並獲取並行邊
            source_node = f"{edge.source_type.value}_{edge.source}"
            target_node = f"{edge.target_type.value}_{edge.target}"

            # 7.處理特殊節點類型邊資訊(意圖識別)
            if edge.source_type == NodeType.QUESTION_CLASSIFIER:
                # 8.更新意圖識別的起點，使用虛擬節點進行拼接
                source_node = f"qc_source_handle_{str(edge.source_handle_id)}"
                non_parallel_nodes.extend([source_node, target_node])

            # 9.處理並行節點
            if target_node not in parallel_edges:
                parallel_edges[target_node] = [source_node]
            else:
                parallel_edges[target_node].append(source_node)

            # 10.檢測特殊節點（開始節點、結束節點），需要寫成兩個if的格式，避免只有一條邊的情況識別失敗
            if edge.source_type == NodeType.START:
                start_node = f"{edge.source_type.value}_{edge.source}"
            if edge.target_type == NodeType.END:
                end_node = f"{edge.target_type.value}_{edge.target}"

        # 11.設置開始和終點
        graph.set_entry_point(start_node)
        graph.set_finish_point(end_node)

        # 12.循環遍歷合併邊
        for target_node, source_nodes in parallel_edges.items():
            # 12.1[更新升級] 循環遍歷意圖識別節點的下一條邊並單獨添加
            source_nodes_tmp = [*source_nodes]
            for item in non_parallel_nodes:
                if item in source_nodes_tmp:
                    source_nodes_tmp.remove(item)
                    graph.add_edge(item, target_node)

            # 12.2[更新升級] 正常添加其他邊
            graph.add_edge(source_nodes_tmp, target_node)

        # 13.構建圖程序並編譯
        return graph.compile()

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """工作流組件基礎run方法"""
        # 1.調用工作流獲取結果資訊
        result = self._workflow.invoke({"inputs": kwargs})

        # 2.提取響應結果的outputs內容作為輸出
        return result.get("outputs", {})

    def stream(
            self,
            input: Input,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        """工作流流式輸出每個節點對應的結果"""
        return self._workflow.stream({"inputs": input})
