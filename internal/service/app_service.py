#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/14 下午11:31
@Author : zsting29@gmail.com
@File   : app_service.py
"""
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Generator, Any
from uuid import UUID

from flask import current_app
from injector import inject
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

from internal.core.agent.agents import FunctionCallAgent, ReACTAgent, AgentQueueManager
from internal.core.agent.entities.agent_entity import AgentConfig
from internal.core.agent.entities.queue_entity import QueueEvent
from internal.core.language_model import LanguageModelManager
from internal.core.language_model.entities.model_entity import ModelFeature, ModelParameterType
from internal.core.memory import TokenBufferMemory
from internal.core.tools.buildin_tools.providers import BuildinProviderManager
from internal.entity.app_entity import DEFAULT_APP_CONFIG, AppStatus, AppConfigType
from internal.entity.audio_entity import ALLOWED_AUDIO_VOICES
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.entity.dataset_entity import RetrievalSource
from internal.entity.workflow_entity import WorkflowStatus
from internal.exception import ForbiddenException, NotFoundException, ValidateErrorException, FailException
from internal.lib.helper import remove_fields, get_value_type
from internal.model import (
    App,
    AppConfigVersion,
    ApiTool,
    Dataset,
    AppDatasetJoin,
    AppConfig,
    Conversation,
    Message,
    Workflow
)
from internal.model.account import Account
from internal.schema.app_schema import (
    DebugChatReq,
    CreateAppReq,
    GetPublishHistoriesWithPageReq,
    GetDebugConversationMessagesWithPageReq,
    GetAppsWithPageReq
)
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .app_config_service import AppConfigService
from .base_service import BaseService
from .conversation_service import ConversationService
from .language_model_service import LanguageModelService
from .retrieval_service import RetrievalService


@inject
@dataclass
class AppService(BaseService):
    """應用服務邏輯"""
    db: SQLAlchemy
    app_config_service: AppConfigService
    language_model_service: LanguageModelService
    retrieval_service: RetrievalService
    conversation_service: ConversationService
    buildin_provider_manager: BuildinProviderManager
    language_model_manager: LanguageModelManager

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        """創建Agent應用服務"""
        # 1.開啟資料庫自動提交上下文
        print('>', account.id)
        with self.db.auto_commit():
            # 2.創建應用記錄，並刷新數據，從而可以拿到應用id
            app = App(
                account_id=account.id,
                name=req.name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 3.添加草稿記錄
            app_config_version = AppConfigVersion(
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 4.為應用添加草稿配置id
            app.draft_app_config_id = app_config_version.id

        # 5.返回創建的應用記錄
        return app

    def get_app(self, app_id: UUID, account: Account) -> App:
        """根據傳遞的id獲取應用的基礎資訊"""
        # 1.查詢資料庫獲取應用基礎資訊
        app = self.get(App, app_id)

        # 2.判斷應用是否存在
        if not app:
            raise NotFoundException("該應用不存在，請核實後重試")

        # 3.判斷當前帳號是否有權限訪問該應用
        if app.account_id != account.id:
            raise ForbiddenException("當前帳號無權限訪問該應用，請核實後嘗試")

        return app

    def update_app(self, app_id: UUID, account: Account, **kwargs) -> App:
        """根據傳遞的應用id+帳號+資訊，更新指定的應用"""
        app = self.get_app(app_id, account)
        self.update(app, **kwargs)
        return app

    def delete_app(self, app_id: UUID, account: Account) -> App:
        """根據傳遞的應用id+帳號，刪除指定的應用資訊，目前僅刪除應用基礎資訊即可"""
        app = self.get_app(app_id, account)
        self.delete(app)
        return app

    def copy_app(self, app_id: UUID, account: Account) -> App:
        """根據傳遞的應用id，拷貝Agent相關資訊並創建一個新Agent"""
        # 1.獲取App+草稿配置，並校驗權限
        app = self.get_app(app_id, account)
        draft_app_config = app.draft_app_config

        # 2.將數據轉換為字典並剔除無用數據
        app_dict = app.__dict__.copy()
        draft_app_config_dict = draft_app_config.__dict__.copy()

        # 3.剔除無用欄位
        app_remove_fields = [
            "id", "app_config_id", "draft_app_config_id", "debug_conversation_id",
            "status", "updated_at", "created_at", "_sa_instance_state",
        ]
        draft_app_config_remove_fields = [
            "id", "app_id", "version", "updated_at", "created_at", "_sa_instance_state",
        ]
        remove_fields(app_dict, app_remove_fields)
        remove_fields(draft_app_config_dict, draft_app_config_remove_fields)

        # 4.開啟資料庫自動提交上下文
        with self.db.auto_commit():
            # 5.創建一個新的應用記錄
            new_app = App(**app_dict, status=AppStatus.DRAFT)
            self.db.session.add(new_app)
            self.db.session.flush()

            # 6.添加草稿配置
            new_draft_app_config = AppConfigVersion(
                **draft_app_config_dict,
                app_id=new_app.id,
                version=0,
            )
            self.db.session.add(new_draft_app_config)
            self.db.session.flush()

            # 7.更新應用的草稿配置id
            new_app.draft_app_config_id = new_draft_app_config.id

        # 8.返回創建好的新應用
        return new_app

    def get_apps_with_page(self, req: GetAppsWithPageReq, account: Account) -> tuple[list[App], Paginator]:
        """根據傳遞的分頁參數獲取當前登入帳號下的應用分頁列表數據"""
        # 1.構建分頁器
        paginator = Paginator(db=self.db, req=req)

        # 2.構建篩選條件
        filters = [App.account_id == account.id]
        if req.search_word.data:
            filters.append(App.name.ilike(f"%{req.search_word.data}%"))

        # 3.執行分頁操作
        apps = paginator.paginate(
            self.db.session.query(App).filter(*filters).order_by(desc("created_at"))
        )

        return apps, paginator

    def get_draft_app_config(self, app_id: UUID, account: Account) -> dict[str, Any]:
        """根據傳遞的應用id，獲取指定的應用草稿配置資訊"""
        app = self.get_app(app_id, account)
        return self.app_config_service.get_draft_app_config(app)

    def update_draft_app_config(
            self,
            app_id: UUID,
            draft_app_config: dict[str, Any],
            account: Account,
    ) -> AppConfigVersion:
        """根據傳遞的應用id+草稿配置修改指定應用的最新草稿"""
        # 1.獲取應用資訊並校驗
        app = self.get_app(app_id, account)

        # 2.校驗傳遞的草稿配置資訊
        draft_app_config = self._validate_draft_app_config(draft_app_config, account)

        # 3.獲取當前應用的最新草稿資訊
        draft_app_config_record = app.draft_app_config
        self.update(
            draft_app_config_record,
            **draft_app_config,
        )

        return draft_app_config_record

    def publish_draft_app_config(self, app_id: UUID, account: Account) -> App:
        """根據傳遞的應用id+帳號，發布/更新指定的應用草稿配置為運行時配置"""
        # 1.獲取應用的資訊以及草稿資訊
        app = self.get_app(app_id, account)
        draft_app_config = self.get_draft_app_config(app_id, account)

        # 2.創建應用運行配置（在這裡暫時不刪除歷史的運行配置）
        app_config = self.create(
            AppConfig,
            app_id=app_id,
            model_config=draft_app_config["model_config"],
            dialog_round=draft_app_config["dialog_round"],
            preset_prompt=draft_app_config["preset_prompt"],
            tools=[
                {
                    "type": tool["type"],
                    "provider_id": tool["provider"]["id"],
                    "tool_id": tool["tool"]["name"],
                    "params": tool["tool"]["params"],
                }
                for tool in draft_app_config["tools"]
            ],

            workflows=[workflow["id"] for workflow in draft_app_config["workflows"]],
            retrieval_config=draft_app_config["retrieval_config"],
            long_term_memory=draft_app_config["long_term_memory"],
            opening_statement=draft_app_config["opening_statement"],
            opening_questions=draft_app_config["opening_questions"],
            speech_to_text=draft_app_config["speech_to_text"],
            text_to_speech=draft_app_config["text_to_speech"],
            suggested_after_answer=draft_app_config["suggested_after_answer"],
            review_config=draft_app_config["review_config"],
        )

        # 3.更新應用關聯的運行時配置以及狀態
        self.update(app, app_config_id=app_config.id, status=AppStatus.PUBLISHED)

        # 4.先刪除原有的知識庫關聯記錄
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == app_id,
            ).delete()

        # 5.新增新的知識庫關聯記錄
        for dataset in draft_app_config["datasets"]:
            self.create(AppDatasetJoin, app_id=app_id, dataset_id=dataset["id"])

        # 6.獲取應用草稿記錄，並移除id、version、config_type、updated_at、created_at欄位
        draft_app_config_copy = app.draft_app_config.__dict__.copy()
        remove_fields(
            draft_app_config_copy,
            ["id", "version", "config_type", "updated_at", "created_at", "_sa_instance_state"],
        )

        # 7.獲取當前最大的發布版本
        max_version = self.db.session.query(func.coalesce(func.max(AppConfigVersion.version), 0)).filter(
            AppConfigVersion.app_id == app_id,
            AppConfigVersion.config_type == AppConfigType.PUBLISHED,
        ).scalar()

        # 8.新增發布歷史配置
        self.create(
            AppConfigVersion,
            version=max_version + 1,
            config_type=AppConfigType.PUBLISHED,
            **draft_app_config_copy,
        )

        return app

    def cancel_publish_app_config(self, app_id: UUID, account: Account) -> App:
        """根據傳遞的應用id+帳號，取消發布指定的應用配置"""
        # 1.獲取應用資訊並校驗權限
        app = self.get_app(app_id, account)

        # 2.檢測下當前應用的狀態是否為已發布
        if app.status != AppStatus.PUBLISHED:
            raise FailException("當前應用未發布，請核實後重試")

        # 3.修改帳號的發布狀態，並清空關聯配置id
        self.update(app, status=AppStatus.DRAFT, app_config_id=None)

        # 4.刪除應用關聯的知識庫資訊
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == app_id,
            ).delete()

        return app

    def get_publish_histories_with_page(
            self,
            app_id: UUID,
            req: GetPublishHistoriesWithPageReq,
            account: Account
    ) -> tuple[list[AppConfigVersion], Paginator]:
        """根據傳遞的應用id+請求數據，獲取指定應用的發布歷史配置列表資訊"""
        # 1.獲取應用資訊並校驗權限
        self.get_app(app_id, account)

        # 2.構建分頁器
        paginator = Paginator(db=self.db, req=req)

        # 3.執行分頁並獲取數據
        app_config_versions = paginator.paginate(
            self.db.session.query(AppConfigVersion).filter(
                AppConfigVersion.app_id == app_id,
                AppConfigVersion.config_type == AppConfigType.PUBLISHED,
            ).order_by(desc("version"))
        )

        return app_config_versions, paginator

    def fallback_history_to_draft(
            self,
            app_id: UUID,
            app_config_version_id: UUID,
            account: Account,
    ) -> AppConfigVersion:
        """根據傳遞的應用id、歷史配置版本id、帳號資訊，回退特定配置到草稿"""
        # 1.校驗應用權限並獲取資訊
        app = self.get_app(app_id, account)

        # 2.查詢指定的歷史版本配置id
        app_config_version = self.get(AppConfigVersion, app_config_version_id)
        if not app_config_version:
            raise NotFoundException("該歷史版本配置不存在，請核實後重試")

        # 3.校驗歷史版本配置資訊（剔除已刪除的工具、知識庫、工作流）
        draft_app_config_dict = app_config_version.__dict__.copy()
        remove_fields(
            draft_app_config_dict,
            ["id", "app_id", "version", "config_type", "updated_at", "created_at", "_sa_instance_state"],
        )

        # 4.校驗歷史版本配置資訊
        draft_app_config_dict = self._validate_draft_app_config(draft_app_config_dict, account)

        # 5.更新草稿配置資訊
        draft_app_config_record = app.draft_app_config
        self.update(
            draft_app_config_record,
            **draft_app_config_dict,
        )

        return draft_app_config_record

    def get_debug_conversation_summary(
            self,
            app_id: UUID,
            account: Account
    ) -> str:
        """根據傳遞的應用id+帳號獲取指定應用的除錯會話長期記憶"""
        # 1.獲取應用資訊並校驗權限
        app = self.get_app(app_id, account)

        # 2.獲取應用的草稿配置，並校驗長期記憶是否啟用
        draft_app_config = self.get_draft_app_config(app_id, account)
        if draft_app_config["long_term_memory"]["enable"] is False:
            raise FailException("該應用並未開啟長期記憶，無法獲取")

        return app.debug_conversation.summary

    def update_debug_conversation_summary(
            self,
            app_id: UUID,
            summary: str,
            account: Account
    ) -> Conversation:
        """根據傳遞的應用id+總結更新指定應用的除錯長期記憶"""
        # 1.獲取應用資訊並校驗權限
        app = self.get_app(app_id, account)

        # 2.獲取應用的草稿配置，並校驗長期記憶是否啟用
        draft_app_config = self.get_draft_app_config(app_id, account)
        if draft_app_config["long_term_memory"]["enable"] is False:
            raise FailException("該應用並未開啟長期記憶，無法獲取")

        # 3.更新應用長期記憶
        debug_conversation = app.debug_conversation
        self.update(debug_conversation, summary=summary)

        return debug_conversation

    def delete_debug_conversation(self, app_id: UUID, account: Account) -> App:
        """根據傳遞的應用id，刪除指定的應用除錯會話"""
        # 1.獲取應用資訊並校驗權限
        app = self.get_app(app_id, account)

        # 2.判斷是否存在debug_conversation_id這個數據，如果不存在表示沒有會話，無需執行任何操作
        if not app.debug_conversation_id:
            return app

        # 3.否則將debug_conversation_id的值重設為None
        self.update(app, debug_conversation_id=None)

        return app

    def debug_chat(
            self,
            app_id: uuid.UUID,
            req: DebugChatReq,
            account: Account
    ) -> Generator:
        """根據傳遞的應用id+提問query向特定的應用發起會話除錯"""
        # 1.獲取應用資訊並校驗權限
        app = self.get_app(app_id, account)

        # 2.獲取應用的最新草稿配置資訊
        draft_app_config = self.get_draft_app_config(app_id, account)

        # 3.獲取當前應用的除錯會話資訊
        debug_conversation = app.debug_conversation

        # 4.新建一條消息記錄
        message = self.create(
            Message,
            app_id=app_id,
            conversation_id=debug_conversation.id,
            invoke_from=InvokeFrom.DEBUGGER,
            created_by=account.id,
            query=req.query.data,
            image_urls=req.image_urls.data,
            status=MessageStatus.NORMAL,
        )

        # 5.從語言模型管理器中載入大語言模型
        llm = self.language_model_service.load_language_model(draft_app_config.get("model_config", {}))

        # 6.實例化TokenBufferMemory用於提取短期記憶
        token_buffer_memory = TokenBufferMemory(
            db=self.db,
            conversation=debug_conversation,
            model_instance=llm,
        )
        history = token_buffer_memory.get_history_prompt_messages(
            message_limit=draft_app_config["dialog_round"],
        )

        # 7.將草稿配置中的tools轉換成LangChain工具
        tools = self.app_config_service.get_langchain_tools_by_tools_config(draft_app_config["tools"])

        # 8.檢測是否關聯了知識庫
        if draft_app_config["datasets"]:
            # 9.構建LangChain知識庫檢索工具
            dataset_retrieval = self.retrieval_service.create_langchain_tool_from_search(
                flask_app=current_app._get_current_object(),
                dataset_ids=[dataset["id"] for dataset in draft_app_config["datasets"]],
                account_id=account.id,
                retrival_source=RetrievalSource.APP,
                **draft_app_config["retrieval_config"],
            )
            tools.append(dataset_retrieval)

        if draft_app_config["workflows"]:
            workflow_tools = self.app_config_service.get_langchain_tools_by_workflow_ids(
                [workflow["id"] for workflow in draft_app_config["workflows"]]
            )
            tools.extend(workflow_tools)

        # 10.根據LLM是否支持tool_call決定使用不同的Agent
        agent_class = FunctionCallAgent if ModelFeature.TOOL_CALL in llm.features else ReACTAgent
        agent = agent_class(
            llm=llm,
            agent_config=AgentConfig(
                user_id=account.id,
                invoke_from=InvokeFrom.DEBUGGER,
                preset_prompt=draft_app_config["preset_prompt"],
                enable_long_term_memory=draft_app_config["long_term_memory"]["enable"],
                tools=tools,
                review_config=draft_app_config["review_config"],
            ),
        )

        agent_thoughts = {}
        for agent_thought in agent.stream({
            "messages": [llm.convert_to_human_message(req.query.data, req.image_urls.data)],
            "history": history,
            "long_term_memory": debug_conversation.summary,
        }):
            # 11.提取thought以及answer
            event_id = str(agent_thought.id)

            # 12.將數據填充到agent_thought，便於儲存到資料庫服務中
            if agent_thought.event != QueueEvent.PING:
                # 13.除了agent_message數據為疊加，其他均為覆蓋
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    if event_id not in agent_thoughts:
                        # 14.初始化智慧體消息事件
                        agent_thoughts[event_id] = agent_thought
                    else:
                        # 15.疊加智慧體消息
                        agent_thoughts[event_id] = agent_thoughts[event_id].copy(update={
                            "thought": agent_thoughts[event_id].thought + agent_thought.thought,
                            # 消息相關數據
                            "message": agent_thought.message,
                            "message_token_count": agent_thought.message_token_count,
                            "message_unit_price": agent_thought.message_unit_price,
                            "message_price_unit": agent_thought.message_price_unit,
                            # 答案相關數據
                            "answer": agent_thoughts[event_id].answer + agent_thought.answer,
                            "answer_token_count": agent_thought.answer_token_count,
                            "answer_unit_price": agent_thought.answer_unit_price,
                            "answer_price_unit": agent_thought.answer_price_unit,
                            # Agent推理統計相關
                            "total_token_count": agent_thought.total_token_count,
                            "total_price": agent_thought.total_price,
                            "latency": agent_thought.latency,
                        })
                else:
                    # 16.處理其他類型事件的消息
                    agent_thoughts[event_id] = agent_thought
            data = {
                **agent_thought.dict(include={
                    "event", "thought", "observation", "tool", "tool_input", "answer",
                    "total_token_count", "total_price", "latency",
                }),
                "id": event_id,
                "conversation_id": str(debug_conversation.id),
                "message_id": str(message.id),
                "task_id": str(agent_thought.task_id),
            }
            yield f"event: {agent_thought.event}\ndata:{json.dumps(data)}\n\n"
        # 22.將消息以及推理過程添加到資料庫
        self.conversation_service.save_agent_thoughts(
            account_id=account.id,
            app_id=app.id,
            app_config=draft_app_config,
            conversation_id=debug_conversation.id,
            message_id=message.id,
            agent_thoughts=[agent_thought for agent_thought in agent_thoughts.values()],
        )

    def _validate_draft_app_config(
            self,
            draft_app_config:
            dict[str, Any],
            account: Account
    ) -> dict[str, Any]:
        """校驗傳遞的應用草稿配置資訊，返回校驗後的數據"""
        # 1.校驗上傳的草稿配置中對應的欄位，至少擁有一個可以更新的配置
        acceptable_fields = [
            "model_config", "dialog_round", "preset_prompt",
            "tools", "workflows", "datasets", "retrieval_config",
            "long_term_memory", "opening_statement", "opening_questions",
            "speech_to_text", "text_to_speech", "suggested_after_answer", "review_config",
        ]

        # 2.判斷傳遞的草稿配置是否在可接受欄位內
        if (
                not draft_app_config
                or not isinstance(draft_app_config, dict)
                or set(draft_app_config.keys()) - set(acceptable_fields)
        ):
            raise ValidateErrorException("草稿配置欄位出錯，請核實後重試")

        # 3.校驗model_config欄位，provider/model使用嚴格校驗(出錯的時候直接拋出)，parameters使用寬鬆校驗，出錯時使用預設值
        if "model_config" in draft_app_config:
            # 3.1 獲取模型配置並判斷數據是否為字典
            model_config = draft_app_config["model_config"]
            if not isinstance(model_config, dict):
                raise ValidateErrorException("模型配置格式錯誤，請核實後重試")

            # 3.2 判斷model_config鍵資訊是否正確
            if set(model_config.keys()) != {"provider", "model", "parameters"}:
                raise ValidateErrorException("模型鍵配置格式錯誤，請核實後重試")

            # 3.3 判斷模型提供者資訊是否正確
            if not model_config["provider"] or not isinstance(model_config["provider"], str):
                raise ValidateErrorException("模型服務提供商類型必須為字串")
            provider = self.language_model_manager.get_provider(model_config["provider"])
            if not provider:
                raise ValidateErrorException("該模型服務提供商不存在，請核實後重試")

            # 3.4 判斷模型資訊是否正確
            if not model_config["model"] or not isinstance(model_config["model"], str):
                raise ValidateErrorException("模型名字必須是否字串")
            model_entity = provider.get_model_entity(model_config["model"])
            if not model_entity:
                raise ValidateErrorException("該服務提供商下不存在該模型，請核實後重試")

            # 3.5 判斷傳遞的parameters是否正確，如果不正確則設置預設值，並剔除多餘欄位，補全未傳遞的欄位
            parameters = {}
            for parameter in model_entity.parameters:
                # 3.6 從model_config中獲取參數值，如果不存在則設置為預設值
                parameter_value = model_config["parameters"].get(parameter.name, parameter.default)

                # 3.7 判斷參數是否必填
                if parameter.required:
                    # 3.8 參數必填，則值不允許為None，如果為None則設置預設值
                    if parameter_value is None:
                        parameter_value = parameter.default
                    else:
                        # 3.9 值非空則校驗數據類型是否正確，不正確則設置預設值
                        if get_value_type(parameter_value) != parameter.type.value:
                            parameter_value = parameter.default
                else:
                    # 3.10 參數非必填，數據非空的情況下需要校驗
                    if parameter_value is not None:
                        if get_value_type(parameter_value) != parameter.type.value:
                            parameter_value = parameter.default

                # 3.11 判斷參數是否存在options，如果存在則數值必須在options中選擇
                if parameter.options and parameter_value not in parameter.options:
                    parameter_value = parameter.default

                # 3.12 參數類型為int/float，如果存在min/max時候需要校驗
                if parameter.type in [
                    ModelParameterType.INT,
                    ModelParameterType.FLOAT
                ] and parameter_value is not None:
                    # 3.13 校驗數值的min/max
                    if (
                            (parameter.min and parameter_value < parameter.min)
                            or (parameter.max and parameter_value > parameter.max)
                    ):
                        parameter_value = parameter.default

                parameters[parameter.name] = parameter_value

            # 3.13 覆蓋Agent配置中的模型配置
            model_config["parameters"] = parameters
            draft_app_config["model_config"] = model_config

        # 4.校驗dialog_round上下文輪數，校驗數據類型以及範圍
        if "dialog_round" in draft_app_config:
            dialog_round = draft_app_config["dialog_round"]
            if not isinstance(dialog_round, int) or not (0 <= dialog_round <= 100):
                raise ValidateErrorException("攜帶上下文輪數範圍為0-100")

        # 5.校驗preset_prompt
        if "preset_prompt" in draft_app_config:
            preset_prompt = draft_app_config["preset_prompt"]
            if not isinstance(preset_prompt, str) or len(preset_prompt) > 2000:
                raise ValidateErrorException("人設與回復邏輯必須是字串，長度在0-2000個字元")

        # 6.校驗tools工具
        if "tools" in draft_app_config:
            tools = draft_app_config["tools"]
            validate_tools = []

            # 6.1 tools類型必須為列表，空列表則代表不綁定任何工具
            if not isinstance(tools, list):
                raise ValidateErrorException("工具列表必須是列表型數據")
            # 6.2 tools的長度不能超過5
            if len(tools) > 5:
                raise ValidateErrorException("Agent綁定的工具數不能超過5")
            # 6.3 循環校驗工具裡的每一個參數
            for tool in tools:
                # 6.4 校驗tool非空並且類型為字典
                if not tool or not isinstance(tool, dict):
                    raise ValidateErrorException("綁定插件工具參數出錯")
                # 6.5 校驗工具的參數是不是type、provider_id、tool_id、params
                if set(tool.keys()) != {"type", "provider_id", "tool_id", "params"}:
                    raise ValidateErrorException("綁定插件工具參數出錯")
                # 6.6 校驗type類型是否為builtin_tool以及api_tool
                if tool["type"] not in ["builtin_tool", "api_tool"]:
                    raise ValidateErrorException("綁定插件工具參數出錯")
                # 6.7 校驗provider_id和tool_id
                if (
                        not tool["provider_id"]
                        or not tool["tool_id"]
                        or not isinstance(tool["provider_id"], str)
                        or not isinstance(tool["tool_id"], str)
                ):
                    raise ValidateErrorException("插件提供者或者插件標識參數出錯")
                # 6.8 校驗params參數，類型為字典
                if not isinstance(tool["params"], dict):
                    raise ValidateErrorException("插件自訂參數格式錯誤")
                # 6.9 校驗對應的工具是否存在，而且需要劃分成builtin_tool和api_tool
                if tool["type"] == "builtin_tool":
                    builtin_tool = self.buildin_provider_manager.get_tool(tool["provider_id"], tool["tool_id"])
                    if not builtin_tool:
                        continue
                else:
                    api_tool = self.db.session.query(ApiTool).filter(
                        ApiTool.provider_id == tool["provider_id"],
                        ApiTool.name == tool["tool_id"],
                        ApiTool.account_id == account.id,
                    ).one_or_none()
                    if not api_tool:
                        continue

                validate_tools.append(tool)

            # 6.10 校驗綁定的工具是否重複
            check_tools = [f"{tool['provider_id']}_{tool['tool_id']}" for tool in validate_tools]
            if len(set(check_tools)) != len(validate_tools):
                raise ValidateErrorException("綁定插件存在重複")

            # 6.11 重新賦值工具
            draft_app_config["tools"] = validate_tools

        # 7.校驗workflow，提取已發布+權限正確的工作流列表進行綁定（更新配置階段不校驗工作流是否可以正常運行）
        if "workflows" in draft_app_config:
            workflows = draft_app_config["workflows"]

            # 7.1 判斷workflows是否為列表
            if not isinstance(workflows, list):
                raise ValidateErrorException("綁定工作流列表參數格式錯誤")
            # 7.2 判斷關聯的工作流列表是否超過5個
            if len(workflows) > 5:
                raise ValidateErrorException("Agent綁定的工作流數量不能超過5個")
            # 7.3 循環校驗工作流的每個參數，類型必須為UUID
            for workflow_id in workflows:
                try:
                    UUID(workflow_id)
                except Exception as _:
                    raise ValidateErrorException("工作流參數必須是UUID")
            # 7.4 判斷是否重複關聯了工作流
            if len(set(workflows)) != len(workflows):
                raise ValidateErrorException("綁定工作流存在重複")
            # 7.5 校驗關聯工作流的權限，剔除不屬於當前帳號，亦或者未發布的工作流
            workflow_records = self.db.session.query(Workflow).filter(
                Workflow.id.in_(workflows),
                Workflow.account_id == account.id,
                Workflow.status == WorkflowStatus.PUBLISHED,
            ).all()
            workflow_sets = set([str(workflow_record.id) for workflow_record in workflow_records])
            draft_app_config["workflows"] = [workflow_id for workflow_id in workflows if workflow_id in workflow_sets]
        # 8.校驗datasets知識庫列表
        if "datasets" in draft_app_config:
            datasets = draft_app_config["datasets"]

            # 8.1 判斷datasets類型是否為列表
            if not isinstance(datasets, list):
                raise ValidateErrorException("綁定知識庫列表參數格式錯誤")
            # 8.2 判斷關聯的知識庫列表是否超過5個
            if len(datasets) > 5:
                raise ValidateErrorException("Agent綁定的知識庫數量不能超過5個")
            # 8.3 循環校驗知識庫的每個參數
            for dataset_id in datasets:
                try:
                    UUID(dataset_id)
                except Exception as e:
                    raise ValidateErrorException("知識庫列表參數必須是UUID")
            # 8.4 判斷是否傳遞了重複的知識庫
            if len(set(datasets)) != len(datasets):
                raise ValidateErrorException("綁定知識庫存在重複")
            # 8.5 校驗綁定的知識庫權限，剔除不屬於當前帳號的知識庫
            dataset_records = self.db.session.query(Dataset).filter(
                Dataset.id.in_(datasets),
                Dataset.account_id == account.id,
            ).all()
            dataset_sets = set([str(dataset_record.id) for dataset_record in dataset_records])
            draft_app_config["datasets"] = [dataset_id for dataset_id in datasets if dataset_id in dataset_sets]

        # 9.校驗retrieval_config檢索配置
        if "retrieval_config" in draft_app_config:
            retrieval_config = draft_app_config["retrieval_config"]

            # 9.1 判斷檢索配置非空且類型為字典
            if not retrieval_config or not isinstance(retrieval_config, dict):
                raise ValidateErrorException("檢索配置格式錯誤")
            # 9.2 校驗檢索配置的欄位類型
            if set(retrieval_config.keys()) != {"retrieval_strategy", "k", "score"}:
                raise ValidateErrorException("檢索配置格式錯誤")
            # 9.3 校驗檢索策略是否正確
            if retrieval_config["retrieval_strategy"] not in ["semantic", "full_text", "hybrid"]:
                raise ValidateErrorException("檢測策略格式錯誤")
            # 9.4 校驗最大召回數量
            if not isinstance(retrieval_config["k"], int) or not (0 <= retrieval_config["k"] <= 10):
                raise ValidateErrorException("最大召回數量範圍為0-10")
            # 9.5 校驗得分/最小匹配度
            if not isinstance(retrieval_config["score"], float) or not (0 <= retrieval_config["score"] <= 1):
                raise ValidateErrorException("最小匹配範圍為0-1")
                # 10.校驗long_term_memory長期記憶配置
            if "long_term_memory" in draft_app_config:
                long_term_memory = draft_app_config["long_term_memory"]

        # 10. 校驗長期記憶格式
        if "long_term_memory" in draft_app_config:
            long_term_memory = draft_app_config["long_term_memory"]

            # 10.1 校驗長期記憶格式
            if not long_term_memory or not isinstance(long_term_memory, dict):
                raise ValidateErrorException("長期記憶設置格式錯誤")
            # 10.2 校驗長期記憶屬性
            if (
                    set(long_term_memory.keys()) != {"enable"}
                    or not isinstance(long_term_memory["enable"], bool)
            ):
                raise ValidateErrorException("長期記憶設置格式錯誤")

        # 11.校驗opening_statement對話開場白
        if "opening_statement" in draft_app_config:
            opening_statement = draft_app_config["opening_statement"]

            # 11.1 校驗對話開場白類型以及長度
            if not isinstance(opening_statement, str) or len(opening_statement) > 2000:
                raise ValidateErrorException("對話開場白的長度範圍是0-2000")

        # 12.校驗opening_questions開場建議問題列表
        if "opening_questions" in draft_app_config:
            opening_questions = draft_app_config["opening_questions"]

            # 12.1 校驗是否為列表，並且長度不超過3
            if not isinstance(opening_questions, list) or len(opening_questions) > 3:
                raise ValidateErrorException("開場建議問題不能超過3個")
            # 12.2 開場建議問題每個元素都是一個字串
            for opening_question in opening_questions:
                if not isinstance(opening_question, str):
                    raise ValidateErrorException("開場建議問題必須是字串")

        # 13.校驗speech_to_text語音轉文本
        if "speech_to_text" in draft_app_config:
            speech_to_text = draft_app_config["speech_to_text"]

            # 13.1 校驗語音轉文本格式
            if not speech_to_text or not isinstance(speech_to_text, dict):
                raise ValidateErrorException("語音轉文本設定格式錯誤")
            # 13.2 校驗語音轉文本屬性
            if (
                    set(speech_to_text.keys()) != {"enable"}
                    or not isinstance(speech_to_text["enable"], bool)
            ):
                raise ValidateErrorException("語音轉文本設定格式錯誤")

        # 14.校驗text_to_speech文本轉語音設置
        if "text_to_speech" in draft_app_config:
            text_to_speech = draft_app_config["text_to_speech"]

            # 14.1 校驗字典格式
            if not isinstance(text_to_speech, dict):
                raise ValidateErrorException("文本轉語音設置格式錯誤")
            # 14.2 校驗欄位類型
            if (
                    set(text_to_speech.keys()) != {"enable", "voice", "auto_play"}
                    or not isinstance(text_to_speech["enable"], bool)
                    or text_to_speech["voice"] not in ALLOWED_AUDIO_VOICES  # 音色
                    or not isinstance(text_to_speech["auto_play"], bool)
            ):
                raise ValidateErrorException("文本轉語音設置格式錯誤")

        # 15.校驗回答後生成建議問題
        if "suggested_after_answer" in draft_app_config:
            suggested_after_answer = draft_app_config["suggested_after_answer"]

            # 10.1 校驗回答後建議問題格式
            if not suggested_after_answer or not isinstance(suggested_after_answer, dict):
                raise ValidateErrorException("回答後建議問題設置格式錯誤")
            # 10.2 校驗回答後建議問題格式
            if (
                    set(suggested_after_answer.keys()) != {"enable"}
                    or not isinstance(suggested_after_answer["enable"], bool)
            ):
                raise ValidateErrorException("回答後建議問題設置格式錯誤")

        # 16.校驗review_config審核配置
        if "review_config" in draft_app_config:
            review_config = draft_app_config["review_config"]

            # 16.1 校驗欄位格式，非空
            if not review_config or not isinstance(review_config, dict):
                raise ValidateErrorException("審核配置格式錯誤")
            # 16.2 校驗欄位資訊
            if set(review_config.keys()) != {"enable", "keywords", "inputs_config", "outputs_config"}:
                raise ValidateErrorException("審核配置格式錯誤")
            # 16.3 校驗enable
            if not isinstance(review_config["enable"], bool):
                raise ValidateErrorException("review.enable格式錯誤")
            # 16.4 校驗keywords
            if (
                    not isinstance(review_config["keywords"], list)
                    or (review_config["enable"] and len(review_config["keywords"]) == 0)
                    or len(review_config["keywords"]) > 100
            ):
                raise ValidateErrorException("review.keywords非空且不能超過100個關鍵字")
            for keyword in review_config["keywords"]:
                if not isinstance(keyword, str):
                    raise ValidateErrorException("review.keywords敏感詞必須是字串")
            # 16.5 校驗inputs_config輸入配置
            if (
                    not review_config["inputs_config"]
                    or not isinstance(review_config["inputs_config"], dict)
                    or set(review_config["inputs_config"].keys()) != {"enable", "preset_response"}
                    or not isinstance(review_config["inputs_config"]["enable"], bool)
                    or not isinstance(review_config["inputs_config"]["preset_response"], str)
            ):
                raise ValidateErrorException("review.inputs_config必須是一個字典")
            # 16.6 校驗outputs_config輸出配置
            if (
                    not review_config["outputs_config"]
                    or not isinstance(review_config["outputs_config"], dict)
                    or set(review_config["outputs_config"].keys()) != {"enable"}
                    or not isinstance(review_config["outputs_config"]["enable"], bool)
            ):
                raise ValidateErrorException("review.outputs_config格式錯誤")
            # 16.7 在開啟審核模組的時候，必須確保inputs_config或者是outputs_config至少有一個是開啟的
            if review_config["enable"]:
                if (
                        review_config["inputs_config"]["enable"] is False
                        and review_config["outputs_config"]["enable"] is False
                ):
                    raise ValidateErrorException("輸入審核和輸出審核至少需要開啟一項")

                if (
                        review_config["inputs_config"]["enable"]
                        and review_config["inputs_config"]["preset_response"].strip() == ""
                ):
                    raise ValidateErrorException("輸入審核預設響應不能為空")

        return draft_app_config

    def stop_debug_chat(
            self,
            app_id: UUID,
            task_id: UUID,
            account: Account
    ) -> None:
        """根據傳遞的應用id+任務id+帳號，停止某個應用的除錯會話，中斷流式事件"""
        # 1.獲取應用資訊並校驗權限
        self.get_app(app_id, account)

        # 2.調用智慧體隊列管理器停止特定任務
        AgentQueueManager.set_stop_flag(task_id, InvokeFrom.DEBUGGER, account.id)

    def get_debug_conversation_messages_with_page(
            self,
            app_id: UUID,
            req: GetDebugConversationMessagesWithPageReq,
            account: Account
    ) -> tuple[list[Message], Paginator]:
        """根據傳遞的應用id+請求數據，獲取除錯會話消息列表分頁數據"""
        # 1.獲取應用資訊並校驗權限
        app = self.get_app(app_id, account)

        # 2.獲取應用的除錯會話
        debug_conversation = app.debug_conversation

        # 3.構建分頁器並構建游標條件
        paginator = Paginator(db=self.db, req=req)
        filters = []
        if req.created_at.data:
            # 4.將時間戳轉換成DateTime
            created_at_datetime = datetime.fromtimestamp(req.created_at.data)
            filters.append(Message.created_at <= created_at_datetime)

        # 5.執行分頁並查詢數據
        messages = paginator.paginate(
            self.db.session.query(Message).options(joinedload(Message.agent_thoughts)).filter(
                Message.conversation_id == debug_conversation.id,
                Message.status.in_([MessageStatus.STOP, MessageStatus.NORMAL]),
                Message.answer != "",
                *filters,
            ).order_by(desc("created_at"))
        )

        return messages, paginator

    def get_published_config(
            self,
            app_id: UUID,
            account: Account
    ) -> dict[str, Any]:
        """根據傳遞的應用id+帳號，獲取應用的發布配置"""
        # 1.獲取應用資訊並校驗權限
        app = self.get_app(app_id, account)

        # 2.構建發布配置並返回
        return {
            "web_app": {
                "token": app.token_with_default,
                "status": app.status,
            }
        }
