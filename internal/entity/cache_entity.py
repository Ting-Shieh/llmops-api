#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/6 下午5:38
@Author : zsting29@gmail.com
@File   : cache_entity.py
"""
# 快取所的過期時間，單位為妙，預設為600
LOCK_EXPIRE_TIME = 600

# 更新文件啟用狀態快取鎖
LOCK_DOCUMENT_UPDATE_ENABLED = "lock:document:update:enabled_{document_id}"

# 更新關鍵字表快取鎖
LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE = "lock:keyword_table:update:keyword_table_{dataset_id}"

# 更新片段啟用狀態快取鎖
LOCK_SEGMENT_UPDATE_ENABLED = "lock:segment:update:enabled_{segment_id}"
