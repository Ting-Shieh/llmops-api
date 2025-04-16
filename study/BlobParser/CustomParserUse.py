#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/29 下午2:44
@Author : zsting29@gmail.com
@File   : CustomParserUse.py
"""
from typing import Iterator

from langchain_core.document_loaders import BaseBlobParser
from langchain_core.documents import Document
from langchain_core.documents.base import Blob


class CustomParser(BaseBlobParser):
    """自定義解析器，用於將傳入文本二進制文件的每一行解析成Document組件"""

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        line_number = 0
        with blob.as_bytes_io() as f:
            for line in f:
                yield Document(
                    page_content=line,
                    metadata={
                        "source": blob.source,
                        "line_number": line_number
                    }
                )
                line_number += 1


# 1.加載數據
blob = Blob.from_path('./test_custom_loader.txt')
parser = CustomParser()
# 2.解析得到文檔數據
documents = list(parser.lazy_parse(blob))
# 3.輸出
print(len(documents))
print(documents)
print(documents[0].metadata)
