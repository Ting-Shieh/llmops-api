#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:47
@Author : zsting29@gmail.com
@File   : question_classifier_entity.py
"""
from langchain_core.pydantic_v1 import Field, validator, BaseModel

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity
from internal.exception import FailException

# 問題分類器系統預設prompt
QUESTION_CLASSIFIER_SYSTEM_PROMPT = """# 角色
你是一個文本分類引擎，負責對輸入的文本進行分類，並返回相應的分類名稱，如果沒有匹配的分類則返回第一個分類，預設分類會以json列表的名稱提供，請注意正確識別。

## 技能
### 技能1：文本分類
- 接收用戶輸入的文本內容。
- 使用自然語言處理技術分析文本特徵。
- 根據預設的分類資訊，將文本準確劃分至相應類別，並返回分類名稱。
- 分類名稱格式為xxx_uuid，例如: qc_source_handle_1e3ac414-52f9-48f5-94fd-fbf4d3fe2df7，請注意識別。

## 預設分類資訊
預設分類資訊如下:
{preset_classes}

## 限制
- 僅處理文本分類相關任務。
- 輸出僅包含分類名稱，不提供額外解釋或資訊。
- 確保分類結果的準確性，避免錯誤分類。
- 使用預設的分類標準進行判斷，不進行主觀解釋。 
- 如果預設的分類沒有符合條件，請直接返回第一個分類。"""


class ClassConfig(BaseModel):
    """問題分類器配置，儲存分類query、連接的節點類型/id"""
    query: str = Field(default="")  # 問題分類對應的query描述
    node_id: str = Field(default="")  # 該分類連接的節點id
    node_type: str = Field(default="")  # 該分類連接的節點類型
    source_handle_id: str = Field(default="")  # 起點句柄id


class QuestionClassifierNodeData(BaseNodeData):
    """問題分類器/意圖識別節點數據"""
    inputs: list[VariableEntity] = Field(default_factory=list)  # 輸入變數資訊
    outputs: list[VariableEntity] = Field(default_factory=lambda: [])
    classes: list[ClassConfig] = Field(default_factory=list)

    @validator("inputs")
    def validate_inputs(cls, value: list[VariableEntity]):
        """校驗輸入變數資訊"""
        # 1.判斷是否只有一個輸入變數，如果有多個則拋出錯誤
        if len(value) != 1:
            raise FailException("問題分類節點輸入變數資訊出錯")

        # 2.判斷輸入變數類型及欄位名稱是否出錯，更新:query支持多種類型
        query_input = value[0]
        if query_input.name != "query" or query_input.required is False:
            raise FailException("問題分類節點輸入變數名字/類型/必填屬性出錯")

        return value

    @validator("outputs")
    def validate_outputs(cls, value: list[VariableEntity]):
        """重寫覆蓋outputs的輸出，讓其變成一個只讀變數"""
        return []
