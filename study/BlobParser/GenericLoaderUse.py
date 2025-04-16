#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/29 下午3:10
@Author : zsting29@gmail.com
@File   : GenericLoaderUse.py
"""
from langchain_community.document_loaders.generic import GenericLoader

loader = GenericLoader.from_filesystem('.', glob="**.txt", show_progress=True)  # , glob="**.txt"

for index, doc in enumerate(loader.lazy_load()):
    print(f"donwload {index} document. file name: {doc.metadata['source']}")
