#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/29 下午12:11
@Author : zsting29@gmail.com
@File   : BaseLoaderUse.py
"""
from typing import Iterator, AsyncIterator

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class CustomLoader(BaseLoader):
    """自定義文檔的加載器，將文本文件的每一行都解析成Document"""

    def __init__(self, file_path):
        self.file_path = file_path

    def lazy_load(self) -> Iterator[Document]:
        # 1. 讀取對應的文件
        with open(self.file_path, encoding="utf-8") as f:
            line_number = 0
            # 2. 提供文件的每一行
            for line in f:
                # 3. 將每一行生成一個Document實例並通過yield返回
                yield Document(
                    page_content=line,
                    metadata={
                        "source": self.file_path,
                        "line_number": line_number
                    }
                )
                line_number += 1

    async def alazy_load(self) -> AsyncIterator[Document]:
        """A lazy loader for Documents."""
        import aiofiles
        # 1. 讀取對應的文件
        async with aiofiles.open(self.file_path, encoding="utf-8") as f:
            line_number = 0
            # 2. 提供文件的每一行
            async for line in f:
                # 3. 將每一行生成一個Document實例並通過yield返回
                yield Document(
                    page_content=line,
                    metadata={
                        "source": self.file_path,
                        "line_number": line_number
                    }
                )
                line_number += 1


loader = CustomLoader('./test_custom_loader.txt')
documents = loader.load()
