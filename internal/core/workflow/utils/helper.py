#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/12/6 下午4:30
@Author : zsting29@gmail.com
@File   : helper.py
"""
from typing import Any

from internal.core.workflow.entities.variable_entity import (
    VariableEntity,
    VariableValueType,
    VARIABLE_TYPE_MAP,
    VARIABLE_TYPE_DEFAULT_VALUE_MAP,
)
from internal.core.workflow.entities.workflow_entity import WorkflowState


def extract_variables_from_state(variables: list[VariableEntity], state: WorkflowState) -> dict[str, Any]:
    """從狀態中提取變數映射值資訊"""
    # 1.構建變數字典資訊
    variables_dict = {}

    # 2.循環遍歷輸入變數實體
    for variable in variables:
        # 3.獲取數據變數類型
        variable_type_cls = VARIABLE_TYPE_MAP.get(variable.type)

        # 4.判斷數據是引用還是直接輸入
        if variable.value.type == VariableValueType.LITERAL:
            variables_dict[variable.name] = variable_type_cls(variable.value.content)
        else:
            # 5.引用or生成數據類型，遍歷節點獲取數據
            for node_result in state["node_results"]:
                if node_result.node_data.id == variable.value.content.ref_node_id:
                    # 6.提取數據並完成數據強制轉換
                    variables_dict[variable.name] = variable_type_cls(node_result.outputs.get(
                        variable.value.content.ref_var_name,
                        VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(variable.type)
                    ))
    return variables_dict
