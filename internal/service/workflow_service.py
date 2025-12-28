#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/28 下午1:45
@Author : zsting29@gmail.com
@File   : workflow_service.py
"""
import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Generator
from uuid import UUID

from flask import request
from injector import inject
from sqlalchemy import desc

from internal.core.tools.buildin_tools.providers import BuildinProviderManager
from internal.core.workflow import Workflow as WorkflowTool
from internal.core.workflow.entities.edge_entity import BaseEdgeData
from internal.core.workflow.entities.node_entity import NodeType, BaseNodeData
from internal.core.workflow.entities.workflow_entity import WorkflowConfig
from internal.core.workflow.nodes import (
    CodeNodeData,
    DatasetRetrievalNodeData,
    EndNodeData,
    HttpRequestNodeData,
    LLMNodeData,
    StartNodeData,
    TemplateTransformNodeData,
    ToolNodeData,
    QuestionClassifierNodeData,
    IterationNodeData
)
from internal.entity.workflow_entity import WorkflowStatus, DEFAULT_WORKFLOW_CONFIG, WorkflowResultStatus
from internal.exception import ValidateErrorException, NotFoundException, ForbiddenException, FailException
from internal.lib.helper import convert_model_to_dict
from internal.model import Account, Workflow, Dataset, ApiTool, WorkflowResult
from internal.schema.workflow_schema import CreateWorkflowReq, GetWorkflowsWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class WorkflowService(BaseService):
    """工作流服務"""
    db: SQLAlchemy
    builtin_provider_manager: BuildinProviderManager

    def create_workflow(self, req: CreateWorkflowReq, account: Account) -> Workflow:
        """根據傳遞的請求資訊創建工作流"""
        # 1.根據傳遞的工作流工具名稱查詢工作流資訊
        check_workflow = self.db.session.query(Workflow).filter(
            Workflow.tool_call_name == req.tool_call_name.data.strip(),
            Workflow.account_id == account.id,
        ).one_or_none()
        if check_workflow:
            raise ValidateErrorException(f"在當前帳號下已創建[{req.tool_call_name.data}]工作流，不支持重名")

        # 2.調用資料庫服務創建工作流
        return self.create(Workflow, **{
            **req.data,
            **DEFAULT_WORKFLOW_CONFIG,
            "account_id": account.id,
            "is_debug_passed": False,
            "status": WorkflowStatus.DRAFT,
            "tool_call_name": req.tool_call_name.data.strip(),
        })

    def get_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """根據傳遞的工作流id，獲取指定的工作流基礎資訊"""
        # 1.查詢資料庫獲取工作流基礎資訊
        workflow = self.get(Workflow, workflow_id)

        # 2.判斷工作流是否存在
        if not workflow:
            raise NotFoundException("該工作流不存在，請核實後重試")

        # 3.判斷當前帳號是否有權限訪問該應用
        if workflow.account_id != account.id:
            raise ForbiddenException("當前帳號無權限訪問該應用，請核實後嘗試")

        return workflow

    def delete_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """根據傳遞的工作流id+帳號資訊，刪除指定的工作流"""
        # 1.獲取工作流基礎資訊並校驗權限
        workflow = self.get_workflow(workflow_id, account)

        # 2.刪除工作流
        self.delete(workflow)

        return workflow

    def update_workflow(self, workflow_id: UUID, account: Account, **kwargs) -> Workflow:
        """根據傳遞的工作流id+請求更新工作流基礎資訊"""
        # 1.獲取工作流基礎資訊並校驗權限
        workflow = self.get_workflow(workflow_id, account)

        # 2.根據傳遞的工具調用名字查詢是否存在重名工作流
        check_workflow = self.db.session.query(Workflow).filter(
            Workflow.tool_call_name == kwargs.get("tool_call_name", "").strip(),
            Workflow.account_id == account.id,
            Workflow.id != workflow.id,
        ).one_or_none()
        if check_workflow:
            raise ValidateErrorException(f"在當前帳號下已創建[{kwargs.get('tool_call_name', '')}]工作流，不支持重名")

        # 3.更新工作流基礎資訊
        self.update(workflow, **kwargs)

        return workflow

    def get_workflows_with_page(
            self, req: GetWorkflowsWithPageReq, account: Account
    ) -> tuple[list[Workflow], Paginator]:
        """根據傳遞的資訊獲取工作流分頁列表數據"""
        # 1.構建分頁器
        paginator = Paginator(db=self.db, req=req)

        # 2.構建篩選器
        filters = [Workflow.account_id == account.id]
        if req.search_word.data:
            filters.append(Workflow.name.ilike(f"%{req.search_word.data}%"))
        if req.status.data:
            filters.append(Workflow.status == req.status.data)

        # 3.分頁查詢數據
        workflows = paginator.paginate(
            self.db.session.query(Workflow).filter(*filters).order_by(desc("created_at"))
        )

        return workflows, paginator

    def update_draft_graph(self, workflow_id: UUID, draft_graph: dict[str, Any], account: Account) -> Workflow:
        """根據傳遞的工作流id+草稿圖配置+帳號更新工作流的草稿圖"""
        # 1.根據傳遞的id獲取工作流並校驗權限
        workflow = self.get_workflow(workflow_id, account)

        # 2.校驗傳遞的草稿圖配置，因為有可能邊有可能還未建立，所以需要校驗關聯的數據
        validate_draft_graph = self._validate_graph(workflow_id, draft_graph, account)

        # 3.更新工作流草稿圖配置，每次修改都將is_debug_passed的值重設為False，該處可以最佳化對比字典裡除position的其他屬性
        self.update(workflow, **{
            "draft_graph": validate_draft_graph,
            "is_debug_passed": False,
        })

        return workflow

    def get_draft_graph(self, workflow_id: UUID, account: Account) -> dict[str, Any]:
        """根據傳遞的工作流id+帳號資訊，獲取指定工作流的草稿配置資訊"""
        # 1.根據傳遞的id獲取工作流並校驗權限
        workflow = self.get_workflow(workflow_id, account)

        # 2.提取草稿圖結構資訊並校驗(不更新校驗後的數據到資料庫)
        draft_graph = workflow.draft_graph
        validate_draft_graph = self._validate_graph(workflow_id, draft_graph, account)

        # 3.循環遍歷節點資訊，為工具節點/知識庫節點附加元數據
        for node in validate_draft_graph["nodes"]:
            if node.get("node_type") == NodeType.TOOL:
                # 4.判斷工具的類型執行不同的操作
                if node.get("tool_type") == "builtin_tool":
                    # 5.節點類型為工具，則附加工具的名稱、圖示、參數等額外資訊
                    provider = self.builtin_provider_manager.get_provider(node.get("provider_id"))
                    if not provider:
                        continue

                    # 6.獲取提供者下的工具實體，並檢測是否存在
                    tool_entity = provider.get_tool_entity(node.get("tool_id"))
                    if not tool_entity:
                        continue

                    # 7.判斷工具的params和草稿中的params是否一致，如果不一致則全部重設為預設值（或者考慮刪除這個工具的引用）
                    param_keys = set([param.name for param in tool_entity.params])
                    params = node.get("params")
                    if set(params.keys()) - param_keys:
                        params = {
                            param.name: param.default
                            for param in tool_entity.params
                            if param.default is not None
                        }

                    # 8.數據校驗成功附加展示資訊
                    provider_entity = provider.provider_entity
                    node["meta"] = {
                        "type": "builtin_tool",
                        "provider": {
                            "id": provider_entity.name,
                            "name": provider_entity.name,
                            "label": provider_entity.label,
                            "icon": f"{request.scheme}://{request.host}/builtin-tools/{provider_entity.name}/icon",
                            "description": provider_entity.description,
                        },
                        "tool": {
                            "id": tool_entity.name,
                            "name": tool_entity.name,
                            "label": tool_entity.label,
                            "description": tool_entity.description,
                            "params": params,
                        }
                    }
                elif node.get("tool_type") == "api_tool":
                    # 9.查詢資料庫獲取對應的工具記錄，並檢測是否存在
                    tool_record = self.db.session.query(ApiTool).filter(
                        ApiTool.provider_id == node.get("provider_id"),
                        ApiTool.name == node.get("tool_id"),
                        ApiTool.account_id == account.id,
                    ).one_or_none()
                    if not tool_record:
                        continue

                    # 10.組裝api工具展示資訊
                    provider = tool_record.provider
                    node["meta"] = {
                        "type": "api_tool",
                        "provider": {
                            "id": str(provider.id),
                            "name": provider.name,
                            "label": provider.name,
                            "icon": provider.icon,
                            "description": provider.description,
                        },
                        "tool": {
                            "id": str(tool_record.id),
                            "name": tool_record.name,
                            "label": tool_record.name,
                            "description": tool_record.description,
                            "params": {},
                        },
                    }
                else:
                    node["meta"] = {
                        "type": "api_tool",
                        "provider": {
                            "id": "",
                            "name": "",
                            "label": "",
                            "icon": "",
                            "description": "",
                        },
                        "tool": {
                            "id": "",
                            "name": "",
                            "label": "",
                            "description": "",
                            "params": {},
                        },
                    }
            elif node.get("node_type") == NodeType.DATASET_RETRIEVAL:
                # 5.節點類型為知識庫檢索，需要附加知識庫的名稱、圖示等資訊
                datasets = self.db.session.query(Dataset).filter(
                    Dataset.id.in_(node.get("dataset_ids", [])),
                    Dataset.account_id == account.id,
                ).all()
                datasets = datasets[:5]
                node["dataset_ids"] = [str(dataset.id) for dataset in datasets]
                node["meta"] = {
                    "datasets": [{
                        "id": dataset.id,
                        "name": dataset.name,
                        "icon": dataset.icon,
                        "description": dataset.description,
                    } for dataset in datasets]
                }
            # 6.[功能升級] 檢查迭代節點工作流配置
            elif node.get("node_type") == NodeType.ITERATION:
                workflows = self.db.session.query(Workflow).filter(
                    Workflow.id.in_(node.get("workflow_ids", [])),
                    Workflow.account_id == account.id,
                    Workflow.status == WorkflowStatus.PUBLISHED,
                ).all()
                workflows = workflows[:1]
                node["workflow_ids"] = [str(workflow.id) for workflow in workflows]
                node["meta"] = {
                    "workflows": [{
                        "id": workflow.id,
                        "name": workflow.name,
                        "icon": workflow.icon,
                        "description": workflow.description,
                    } for workflow in workflows]
                }

        return validate_draft_graph

    def debug_workflow(self, workflow_id: UUID, inputs: dict[str, Any], account: Account) -> Generator:
        """除錯指定的工作流API介面，該介面為流式事件輸出"""
        # 1.根據傳遞的id獲取工作流並校驗權限
        workflow = self.get_workflow(workflow_id, account)

        # 2.創建工作流工具
        workflow_tool = WorkflowTool(workflow_config=WorkflowConfig(
            account_id=account.id,
            name=workflow.tool_call_name,
            description=workflow.description,
            nodes=workflow.draft_graph.get("nodes", []),
            edges=workflow.draft_graph.get("edges", []),
        ))

        def handle_stream() -> Generator:
            # 3.定義變數儲存所有節點運行結果
            node_results = []

            # 4.添加資料庫工作流運行結果記錄
            workflow_result = self.create(WorkflowResult, **{
                "app_id": None,
                "account_id": account.id,
                "workflow_id": workflow.id,
                "graph": workflow.draft_graph,
                "state": [],
                "latency": 0,
                "status": WorkflowResultStatus.RUNNING,
            })

            # 4.調用stream服務獲取工具資訊
            start_at = time.perf_counter()
            try:
                for chunk in workflow_tool.stream(inputs):
                    # 5.chunk的格式為:{"node_name": WorkflowState}，所以需要取出節點響應結構的第1個key
                    first_key = next(iter(chunk))

                    # 6.取出各個節點的運行結果
                    # 6.1 因為存在虛擬節點，所以需要判斷是否執行當前循環
                    if len(chunk[first_key]["node_results"]) == 0:
                        continue
                    node_result = chunk[first_key]["node_results"][0]
                    node_result_dict = convert_model_to_dict(node_result)
                    node_results.append(node_result_dict)

                    # 7.組裝響應數據並流式事件輸出
                    data = {
                        "id": str(uuid.uuid4()),
                        **node_result_dict,
                    }
                    yield f"event: workflow\ndata: {json.dumps(data)}\n\n"

                # 7.流式輸出完畢後，將結果儲存到資料庫中
                self.update(workflow_result, **{
                    "status": WorkflowResultStatus.SUCCEEDED,
                    "state": node_results,
                    "latency": (time.perf_counter() - start_at),
                })
                self.update(workflow, **{
                    "is_debug_passed": True,
                })
            except Exception as e:
                logging.exception("執行工作流發生錯誤, 錯誤資訊: %(error)s", {"error": e})
                self.update(workflow_result, **{
                    "status": WorkflowResultStatus.FAILED,
                    "state": node_results,
                    "latency": (time.perf_counter() - start_at)
                })

        return handle_stream()

    def publish_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """根據傳遞的工作流id，發布指定的工作流"""
        # 1.根據傳遞的id獲取工作流並校驗權限
        workflow = self.get_workflow(workflow_id, account)

        # 2.校驗工作流是否除錯通過
        if workflow.is_debug_passed is False:
            raise FailException("該工作流未除錯通過，請除錯通過後發布")

        # 3.使用WorkflowConfig二次校驗，如果校驗失敗則不發布
        try:
            WorkflowConfig(
                account_id=account.id,
                name=workflow.tool_call_name,
                description=workflow.description,
                nodes=workflow.draft_graph.get("nodes", []),
                edges=workflow.draft_graph.get("edges", []),
            )
        except Exception:
            self.update(workflow, **{
                "is_debug_passed": False,
            })
            raise ValidateErrorException("工作流配置校驗失敗，請核實後重試")

        # 4.更新工作流的發布狀態
        self.update(workflow, **{
            "graph": workflow.draft_graph,
            "status": WorkflowStatus.PUBLISHED,
            "is_debug_passed": False,
        })

        return workflow

    def cancel_publish_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """取消發布指定的工作流"""
        # 1.根據傳遞的id獲取工作流並校驗權限
        workflow = self.get_workflow(workflow_id, account)

        # 2.校驗工作流是否為已發布的狀態
        if workflow.status != WorkflowStatus.PUBLISHED:
            raise FailException("該工作流未發布無法取消發布")

        # 3.更新發布狀態並刪除運行圖草稿配置
        self.update(workflow, **{
            "graph": {},
            "status": WorkflowStatus.DRAFT,
            "is_debug_passed": False,
        })

        return workflow

    def _validate_graph(self, workflow_id: UUID, graph: dict[str, Any], account: Account) -> dict[str, Any]:
        """校驗傳遞的graph資訊，涵蓋nodes和edges對應的數據，該函數使用相對寬鬆的校驗方式，並且因為是草稿，不需要校驗節點與邊的關係"""
        # 1.提取nodes和edges數據
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # 2.構建節點類型與節點數據類映射
        node_data_classes = {
            NodeType.START: StartNodeData,
            NodeType.END: EndNodeData,
            NodeType.LLM: LLMNodeData,
            NodeType.TEMPLATE_TRANSFORM: TemplateTransformNodeData,
            NodeType.DATASET_RETRIEVAL: DatasetRetrievalNodeData,
            NodeType.CODE: CodeNodeData,
            NodeType.TOOL: ToolNodeData,
            NodeType.HTTP_REQUEST: HttpRequestNodeData,
            # 添加意圖識別類型節點與迭代節點
            NodeType.QUESTION_CLASSIFIER: QuestionClassifierNodeData,
            NodeType.ITERATION: IterationNodeData,
        }

        # 3.循環校驗nodes中各個節點對應的數據
        node_data_dict: dict[UUID, BaseNodeData] = {}
        start_nodes = 0
        end_nodes = 0
        for node in nodes:
            try:
                # 4.校驗傳遞的node數據是不是字典，如果不是則跳過當前數據
                if not isinstance(node, dict):
                    raise ValidateErrorException("工作流節點數據類型出錯，請核實後重試")

                # 5.提取節點的node_type類型，並判斷類型是否正確
                node_type = node.get("node_type", "")
                node_data_cls = node_data_classes.get(node_type, None)
                if node_data_cls is None:
                    raise ValidateErrorException("工作流節點類型出錯，請核實後重試")

                # 6.實例化節點數據類型，如果出錯則跳過當前數據
                node_data = node_data_cls(**node)

                # 7.判斷節點id是否唯一，如果不唯一，則將當前節點清除
                if node_data.id in node_data_dict:
                    raise ValidateErrorException("工作流節點id必須唯一，請核實後重試")

                # 8.判斷節點title是否唯一，如果不唯一，則將當前節點清除
                if any(item.title.strip() == node_data.title.strip() for item in node_data_dict.values()):
                    raise ValidateErrorException("工作流節點title必須唯一，請核實後重試")

                # 9.對特殊節點進行判斷，涵蓋開始/結束/知識庫檢索/工具
                if node_data.node_type == NodeType.START:
                    if start_nodes >= 1:
                        raise ValidateErrorException("工作流中只允許有1個開始節點")
                    start_nodes += 1
                elif node_data.node_type == NodeType.END:
                    if end_nodes >= 1:
                        raise ValidateErrorException("工作流中只允許有1個結束節點")
                    end_nodes += 1
                elif node_data.node_type == NodeType.DATASET_RETRIEVAL:
                    # 10.剔除關聯知識庫列表中不屬於當前帳戶的數據
                    datasets = self.db.session.query(Dataset).filter(
                        Dataset.id.in_(node_data.dataset_ids[:5]),
                        Dataset.account_id == account.id,
                    ).all()
                    node_data.dataset_ids = [dataset.id for dataset in datasets]
                # 11.[升級更新] 判斷類型為迭代節點，剔除不屬於當前帳戶並且未發布的工作流
                elif node_data.node_type == NodeType.ITERATION:
                    workflows = self.db.session.query(Workflow).filter(
                        Workflow.id.in_(node_data.workflow_ids[:1]),
                        Workflow.account_id == account.id,
                        Workflow.status == WorkflowStatus.PUBLISHED,
                    ).all()
                    # 11.[升級更新] 剔除當前工作流，迭代節點不能內嵌本身（這塊還可以繼續升級，雙方不能內嵌）
                    node_data.workflow_ids = [workflow.id for workflow in workflows if workflow.id != workflow_id]

                # 11.將數據添加到node_data_dict中
                node_data_dict[node_data.id] = node_data
            except Exception:
                continue

        # 14.循環校驗edges中各個節點對應的數據
        edge_data_dict: dict[UUID, BaseEdgeData] = {}
        for edge in edges:
            try:
                # 15.邊類型為非字典則拋出錯誤，否則轉換成BaseEdgeData
                if not isinstance(edge, dict):
                    raise ValidateErrorException("工作流邊數據類型出錯，請核實後重試")
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
            except Exception:
                continue

        return {
            "nodes": [convert_model_to_dict(node_data) for node_data in node_data_dict.values()],
            "edges": [convert_model_to_dict(edge_data) for edge_data in edge_data_dict.values()],
        }
