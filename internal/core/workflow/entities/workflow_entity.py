#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:25
@Author : zsting29@gmail.com
@File   : workflow_entity.py
"""
import re
from collections import defaultdict, deque
from typing import Any, TypedDict, Annotated
from uuid import UUID

from langchain_core.pydantic_v1 import BaseModel, Field, root_validator

from internal.exception import ValidateErrorException
from .edge_entity import BaseEdgeData
from .node_entity import BaseNodeData, NodeResult, NodeType
from .variable_entity import VariableEntity, VariableValueType

# 工作流配置校驗資訊
WORKFLOW_CONFIG_NAME_PATTERN = r'^[A-Za-z_][A-Za-z0-9_]*$'
WORKFLOW_CONFIG_DESCRIPTION_MAX_LENGTH = 1024


def _process_dict(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """工作流狀態字典歸納函數"""
    # 1.處理left和right出現空的情況
    left = left or {}
    right = right or {}

    # 2.合併更新字典並返回
    return {**left, **right}


def _process_node_results(left: list[NodeResult], right: list[NodeResult]) -> list[NodeResult]:
    """工作流狀態節點結果列表歸納函數"""
    # 1.處理left和right出現空的情況
    left = left or []
    right = right or []

    # 2.合併列表更新後返回
    return left + right


class WorkflowConfig(BaseModel):
    """工作流配置資訊"""
    account_id: UUID  # 用戶的唯一標識數據
    name: str = ""  # 工作流名稱，必須是英文
    description: str = ""  # 工作流描述資訊，用於告知LLM什麼時候需要調用工作流
    nodes: list[BaseNodeData] = Field(default_factory=list)  # 工作流對應的節點列表資訊
    edges: list[BaseEdgeData] = Field(default_factory=list)  # 工作流對應的邊列表資訊

    @root_validator(pre=True)
    def validate_workflow_config(cls, values: dict[str, Any]):
        """自訂校驗函數，用於校驗工作流配置中的所有參數資訊"""
        # 1.獲取工作流名字name，並校驗是否符合規則
        name = values.get("name", None)
        if not name or not re.match(WORKFLOW_CONFIG_NAME_PATTERN, name):
            raise ValidateErrorException("工作流名字僅支持字母、數字和下劃線，且以字母/下劃線為開頭")

        # 2.校驗工作流的描述資訊，該描述資訊是傳遞給LLM使用，長度不能超過1024個字元
        description = values.get("description", None)
        if not description or len(description) > WORKFLOW_CONFIG_DESCRIPTION_MAX_LENGTH:
            raise ValidateErrorException("工作流描述資訊長度不能超過1024個字元")

        # 3.獲取節點和邊列表資訊
        nodes = values.get("nodes", [])
        edges = values.get("edges", [])

        # 4.校驗nodes/edges數據類型和內容不能為空
        if not isinstance(nodes, list) or len(nodes) <= 0:
            raise ValidateErrorException("工作流節點列表資訊錯誤，請核實後重試")
        if not isinstance(edges, list) or len(edges) <= 0:
            raise ValidateErrorException("工作流邊列表資訊錯誤，請核實後重試")

        # 5.節點數據類映射
        from internal.core.workflow.nodes import (
            CodeNodeData,
            DatasetRetrievalNodeData,
            EndNodeData,
            HttpRequestNodeData,
            LLMNodeData,
            StartNodeData,
            TemplateTransformNodeData,
            ToolNodeData,
            # 新增意圖識別類型數據與迭代節點
            QuestionClassifierNodeData,
            IterationNodeData,
        )
        node_data_classes = {
            NodeType.START: StartNodeData,
            NodeType.END: EndNodeData,
            NodeType.LLM: LLMNodeData,
            NodeType.TEMPLATE_TRANSFORM: TemplateTransformNodeData,
            NodeType.DATASET_RETRIEVAL: DatasetRetrievalNodeData,
            NodeType.CODE: CodeNodeData,
            NodeType.TOOL: ToolNodeData,
            NodeType.HTTP_REQUEST: HttpRequestNodeData,
            # 新增意圖識別類與迭代節點
            NodeType.QUESTION_CLASSIFIER: QuestionClassifierNodeData,
            NodeType.ITERATION: IterationNodeData,
        }

        # 5.循環遍歷所有節點
        node_data_dict: dict[UUID, BaseNodeData] = {}
        start_nodes = 0
        end_nodes = 0
        for node in nodes:
            # 6.判斷每個節點數據類型為字典
            if not isinstance(node, dict):
                raise ValidateErrorException("工作流節點數據類型出錯，請核實後重試")

            # 7.獲取節點的類型並判斷類型是否存在
            node_type = node.get("node_type", "")
            node_data_cls = node_data_classes.get(node_type, None)
            if not node_data_cls:
                raise ValidateErrorException("工作流節點類型出錯，請核實後重試")

            # 8.實例化節點數據，使用BaseModel規則進行校驗
            node_data = node_data_cls(**node)

            # 9.判斷開始和結束節點是否唯一
            if node_data.node_type == NodeType.START:
                if start_nodes >= 1:
                    raise ValidateErrorException("工作流中只允許有1個開始節點")
                start_nodes += 1
            elif node_data.node_type == NodeType.END:
                if end_nodes >= 1:
                    raise ValidateErrorException("工作流中只允許有1個結束節點")
                end_nodes += 1

            # 10.判斷nodes節點數據id是否唯一
            if node_data.id in node_data_dict:
                raise ValidateErrorException("工作流節點id必須唯一，請核實後重試")

            # 11.判斷nodes節點數據title是否唯一
            if any(item.title.strip() == node_data.title.strip() for item in node_data_dict.values()):
                raise ValidateErrorException("工作流節點title必須唯一，請核實後重試")

            # 12.將數據添加到node_data_dict中
            node_data_dict[node_data.id] = node_data

        # 13.循環遍歷edges數據
        edge_data_dict: dict[UUID, BaseEdgeData] = {}
        for edge in edges:
            # 14.判斷邊數據類型為字典
            if not isinstance(edge, dict):
                raise ValidateErrorException("工作流邊數據類型出錯，請核實後重試")

            # 15.實例化邊數據，使用BaseModel規則進行校驗
            edge_data = BaseEdgeData(**edge)

            # 16.校驗邊edges的id是否唯一
            if edge_data.id in edge_data_dict:
                raise ValidateErrorException("工作流邊數據id必須唯一，請核實後重試")

            # 17.校驗邊中的source/target/source_type/target_type必須和nodes對得上
            if (
                    edge_data.source not in node_data_dict
                    or edge_data.source_type != node_data_dict[edge_data.source].node_type
                    or edge_data.target not in node_data_dict
                    or edge_data.target_type != node_data_dict[edge_data.target].node_type
            ):
                raise ValidateErrorException("工作流邊起點/終點對應的節點不存在或類型錯誤，請核實後重試")

            # 18[升級更新].校驗邊Edges裡的邊必須唯一(source+target+source_handle_id必須唯一)，適配意圖識別節點
            if any(
                    (
                            item.source == edge_data.source
                            and item.target == edge_data.target
                            and item.source_handle_id == edge_data.source_handle_id
                    )
                    for item in edge_data_dict.values()
            ):
                raise ValidateErrorException("工作流邊數據不能重複添加")

            # 19.基礎數據校驗通過，將數據添加到edge_data_dict中
            edge_data_dict[edge_data.id] = edge_data

        # 20.構建鄰接表、逆鄰接表、入度以及出度
        adj_list = cls._build_adj_list(edge_data_dict.values())
        reverse_adj_list = cls._build_reverse_adj_list(edge_data_dict.values())
        in_degree, out_degree = cls._build_degrees(edge_data_dict.values())

        # 21.從邊的關係中校驗是否有唯一的開始/結束節點(入度為0即為開始，出度為0即為結束)
        start_nodes = [node_data for node_data in node_data_dict.values() if in_degree[node_data.id] == 0]
        end_nodes = [node_data for node_data in node_data_dict.values() if out_degree[node_data.id] == 0]
        if (
                len(start_nodes) != 1
                or len(end_nodes) != 1
                or start_nodes[0].node_type != NodeType.START
                or end_nodes[0].node_type != NodeType.END
        ):
            raise ValidateErrorException("工作流中有且只有一個開始/結束節點作為圖結構的起點和終點")

        # 22.獲取唯一的開始節點
        start_node_data = start_nodes[0]

        # 23.使用edges邊資訊校驗圖的連通性，確保沒有孤立的節點
        if not cls._is_connected(adj_list, start_node_data.id):
            raise ValidateErrorException("工作流中存在不可到達節點，圖不聯通，請核實後重試")

        # 24.校驗edges中是否存在環路（即循環邊結構）
        if cls._is_cycle(node_data_dict.values(), adj_list, in_degree):
            raise ValidateErrorException("工作流中存在環路，請核實後重試")

        # 25.校驗nodes+edges中的數據引用是否正確，即inputs/outputs對應的數據
        cls._validate_inputs_ref(node_data_dict, reverse_adj_list)

        # 26.更新values值
        values["nodes"] = list(node_data_dict.values())
        values["edges"] = list(edge_data_dict.values())

        return values

    @classmethod
    def _is_connected(cls, adj_list: defaultdict[Any, list], start_node_id: UUID) -> bool:
        """根據傳遞的鄰接表+開始節點id，使用BFS廣度優先搜索遍歷，檢查圖是否流通"""
        # 1.記錄已訪問的節點
        visited = set()

        # 2.創建雙向隊列，並記錄開始訪問節點對應的id
        queue = deque([start_node_id])
        visited.add(start_node_id)

        # 3.循環遍歷隊列，廣度優先搜索節點對應的子節點
        while queue:
            node_id = queue.popleft()
            for neighbor in adj_list[node_id]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # 4.計算已訪問的節點數量是否和總結點數相等，如果不相等則表示存在孤立節點，圖不流通
        return len(visited) == len(adj_list)

    @classmethod
    def _is_cycle(
            cls,
            nodes: list[BaseNodeData],
            adj_list: defaultdict[Any, list],
            in_degree: defaultdict[Any, int],
    ) -> bool:
        """根據傳遞的節點列表、鄰接表、入度數據，使用拓撲排序(Kahn算法)檢測圖中是否存在環，如果存在則返回True，不存在則返回False"""
        # 1.儲存所有入度為0的節點id，即開始節點
        zero_in_degree_nodes = deque([node.id for node in nodes if in_degree[node.id] == 0])

        # 2.記錄已訪問的節點數
        visited_count = 0

        # 3.循環遍歷入度為0的節點資訊
        while zero_in_degree_nodes:
            # 4.從隊列左側取出一個入度為0的節點，並記錄訪問+1
            node_id = zero_in_degree_nodes.popleft()
            visited_count += 1

            # 5.循環遍歷取到的節點的所有子節點
            for neighbor in adj_list[node_id]:
                # 6.將子節點的入度-1，並判斷是否為0，如果是則添加到隊列中
                in_degree[neighbor] -= 1

                # 7.Kahn算法的核心是，如果存在環，那麼至少有一個非結束節點的入度大於等於2，並且該入度無法消減到0
                #   這就會導致該節點後續的所有子節點在該算法下都無法瀏覽，那麼訪問次數肯定小於總節點數
                if in_degree[neighbor] == 0:
                    zero_in_degree_nodes.append(neighbor)

        # 8.判斷訪問次數和總結點數是否相等，如果不等/小於則說明存在環
        return visited_count != len(nodes)

    @classmethod
    def _validate_inputs_ref(
            cls,
            node_data_dict: dict[UUID, BaseNodeData],
            reverse_adj_list: defaultdict[Any, list],
    ) -> None:
        """校驗輸入數據引用是否正確，如果出錯則直接拋出異常"""
        # 1.循環遍歷所有節點數據逐個處理
        for node_data in node_data_dict.values():
            # 2.提取該節點的所有前置節點
            predecessors = cls._get_predecessors(reverse_adj_list, node_data.id)

            # 3.如果節點數據類型不是START則校驗輸入數據引用（因為開始節點不需要校驗）
            if node_data.node_type != NodeType.START:
                # 4.根據節點類型從inputs或者是outputs中提取需要校驗的數據
                variables: list[VariableEntity] = (
                    node_data.inputs if node_data.node_type != NodeType.END
                    else node_data.outputs
                )

                # 5.循環遍歷所有需要校驗的變數資訊
                for variable in variables:
                    # 6.如果變數類型為引用，則需要校驗
                    if variable.value.type == VariableValueType.REF:
                        # 7.判斷前置節點是否為空，或者引用id不在前置節點內，則直接拋出錯誤
                        if (
                                len(predecessors) <= 0
                                or variable.value.content.ref_node_id not in predecessors
                        ):
                            raise ValidateErrorException(f"工作流節點[{node_data.title}]引用數據出錯，請核實後重試")

                        # 8.提取數據引用的前置節點數據
                        ref_node_data = node_data_dict.get(variable.value.content.ref_node_id)

                        # 9.獲取引用變數列表，如果是開始節點則從inputs中獲取數據，否則從outputs中獲取數據
                        ref_variables = (
                            ref_node_data.inputs if ref_node_data.node_type == NodeType.START
                            else ref_node_data.outputs
                        )

                        # 10.判斷引用變數列表中是否存在該引用名字
                        if not any(
                                ref_variable.name == variable.value.content.ref_var_name
                                for ref_variable in ref_variables
                        ):
                            raise ValidateErrorException(
                                f"工作流節點[{node_data.title}]引用了不存在的節點變數，請核實後重試")

    @classmethod
    def _build_adj_list(cls, edges: list[BaseEdgeData]) -> defaultdict[Any, list]:
        """構建鄰接表，鄰接表的key為節點的id，值為該節點的所有直接子節點(後繼節點)"""
        adj_list = defaultdict(list)
        for edge in edges:
            adj_list[edge.source].append(edge.target)
        return adj_list

    @classmethod
    def _build_reverse_adj_list(cls, edges: list[BaseEdgeData]) -> defaultdict[Any, list]:
        """構建逆鄰接表，逆鄰接表的key是每個節點的id，值為該節點的直接父節點"""
        reverse_adj_list = defaultdict(list)
        for edge in edges:
            reverse_adj_list[edge.target].append(edge.source)
        return reverse_adj_list

    @classmethod
    def _build_degrees(cls, edges: list[BaseEdgeData]) -> tuple[defaultdict[Any, int], defaultdict[Any, int]]:
        """根據傳遞的邊資訊，計算每個節點的入度(in_degree)和出度(out_degree)
           in_degree: 指有多少個節點指向該節點
           out_degree: 該節點指向多少個其他節點
        """
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)

        for edge in edges:
            in_degree[edge.target] += 1
            out_degree[edge.source] += 1

        return in_degree, out_degree

    @classmethod
    def _get_predecessors(cls, reverse_adj_list: defaultdict[Any, list], target_node_id: UUID) -> list[UUID]:
        """根據傳遞的逆鄰接表+目標節點id，獲取該節點的所有前置節點"""
        visited = set()
        predecessors = []

        def dfs(node_id):
            """使用廣度搜索優先算法遍歷所有的前置節點"""
            if node_id not in visited:
                visited.add(node_id)
                if node_id != target_node_id:
                    predecessors.append(node_id)
                for neighbor in reverse_adj_list[node_id]:
                    dfs(neighbor)

        dfs(target_node_id)

        return predecessors


class WorkflowState(TypedDict):
    """工作流圖程序狀態字典"""
    inputs: Annotated[dict[str, Any], _process_dict]  # 工作流的最初始輸入，也就是工具輸入
    outputs: Annotated[dict[str, Any], _process_dict]  # 工作流的最終輸出結果，也就是工具輸出
    node_results: Annotated[list[NodeResult], _process_node_results]  # 各節點的運行結果
