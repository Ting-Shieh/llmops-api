#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/29 下午3:02
@Author : zsting29@gmail.com
@File   : FileSystemBlobLoaderUse.py
"""
from langchain_community.document_loaders import FileSystemBlobLoader

loader = FileSystemBlobLoader('./test_custom_loader.txt', show_progress=True)

for b in loader.yield_blobs():
    # print(b.source)
    # print(b.data)
    print(b.as_string())
    print("---------")
