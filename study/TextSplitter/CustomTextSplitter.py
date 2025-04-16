#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/30 下午5:47
@Author : zsting29@gmail.com
@File   : CustomTextSplitter.py
"""
from typing import List

import jieba.analyse
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_text_splitters import TextSplitter


class CustomTextSplitter(TextSplitter):
    """自定義文本分割器"""

    def __init__(self, seperator: str, top_k: int = 10, **kwargs) -> None:
        """構造函數，傳遞分割器還有需要提取的關鍵詞數，默認為10"""
        super().__init__(**kwargs)
        self._seperator = seperator
        self._top_k = top_k

    def split_text(self, text: str) -> List[str]:
        """傳遞對應的文本執行分割並提取分割數據的關鍵詞，組成文檔列表返回"""
        # 1. 根據傳遞的分隔符號分割傳入文本
        split_texts = text.split(self._seperator)
        # 2.提取分割出來的每一段文本關鍵詞，數量為self._top_k個
        text_keywords = []
        for split_text in split_texts:
            text_keywords.append(
                jieba.analyse.extract_tags(split_text, self._top_k)
            )
        # 3.將關鍵時用逗號進行拼接足成字符串列表並返回
        return [",".join(keywords) for keywords in text_keywords]


# 1.創建加載器與分割器
loader = UnstructuredFileLoader("./protein.txt")
text_splitter = CustomTextSplitter("\n\n")

# 2.加載文檔並分割
documents = loader.load()
chunks = text_splitter.split_documents(documents)

# 3.循環文檔訊息
for chunk in chunks:
    print(f"文檔庫內容:{chunk.page_content}")
