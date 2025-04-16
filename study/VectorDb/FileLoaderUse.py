#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/27 下午11:51
@Author : zsting29@gmail.com
@File   : FileLoaderUse.py
"""
from langchain_community.document_loaders import UnstructuredFileLoader

loader = UnstructuredFileLoader("./章节介绍.pptx")
documents = loader.load()

print(documents)
