#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:47
@Author : zsting29@gmail.com
@File   : question_classifier_node.py
"""
import json
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.constants import END

from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .question_classifier_entity import QuestionClassifierNodeData, QUESTION_CLASSIFIER_SYSTEM_PROMPT


class QuestionClassifierNode(BaseNode):
    """問題分類器節點"""
    node_data: QuestionClassifierNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> str:
        """覆蓋重寫invoke實現問題分類器節點，執行問題分類後返回節點的名稱，如果LLM判斷錯誤默認返回第一個節點名稱"""
        # 1.企圖節點輸入變數字典映射
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 2.構建問題分類提示prompt模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", QUESTION_CLASSIFIER_SYSTEM_PROMPT),
            ("human", "{query}"),
        ])

        # 3.創建LLM實例用戶端，使用gpt-4o-mini作為基座模型，並配置溫度與最大輸出tokens
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=512,
        )

        # 4.構建分類鏈
        chain = prompt | llm | StrOutputParser()

        # 5.獲取分類調用結果
        node_flag = chain.invoke({
            "preset_classes": json.dumps(
                [
                    {
                        "query": class_config.query,
                        "class": f"qc_source_handle_{str(class_config.source_handle_id)}"
                    } for class_config in self.node_data.classes
                ]
            ),
            "query": inputs_dict.get("query", "用戶沒有輸入任何內容")
        })

        # 6.獲取所有分類資訊
        all_classes = [f"qc_source_handle_{str(item.source_handle_id)}" for item in self.node_data.classes]

        # 7.檢測獲取的分類標識是否在規定列表內，並提取節點標識
        if len(all_classes) == 0:
            node_flag = END
        elif node_flag not in all_classes:
            node_flag = all_classes[0]

        return node_flag
