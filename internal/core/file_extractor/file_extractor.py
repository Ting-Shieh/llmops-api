#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/3 下午9:09
@Author : zsting29@gmail.com
@File   : file_extractor.py
"""
import os.path
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import requests
from injector import inject
from langchain_community.document_loaders import UnstructuredExcelLoader, UnstructuredPDFLoader, \
    UnstructuredMarkdownLoader, UnstructuredHTMLLoader, UnstructuredCSVLoader, UnstructuredPowerPointLoader, \
    UnstructuredXMLLoader, UnstructuredFileLoader, TextLoader, UnstructuredImageLoader
from langchain_core.documents import Document as LCDocument

from internal.model import UploadFile
from internal.service.gcs_service import GcsService


@inject
@dataclass
class FileExtractor:
    """文件提取器，用於將遠程文件，upload_file紀錄加載成LangChain對應的文檔或字符串"""
    gcs_service: GcsService

    def load(
            self,
            upload_file: UploadFile,
            return_text: bool = False,
            is_unstructured: bool = False
    ) -> Union[list[LCDocument], str]:
        """加載傳入的upload_file紀錄，返回LangChain文檔列表或字符串"""
        # 1.創建一個臨時文件夾
        with tempfile.TemporaryDirectory() as temp_dir:
            # 2.構建一個臨時文件路徑
            file_path = os.path.join(
                temp_dir,
                os.path.basename(upload_file.key)
            )

            # 3.將對象儲存的文件下載到本地
            self.gcs_service.download_file(upload_file.key, file_path)

            # 4.從指定的路徑中加載文件
            return self.load_from_file(file_path, return_text, is_unstructured)

    @classmethod
    def load_from_url(
            cls,
            url: str,
            return_text: bool = False
    ) -> Union[list[LCDocument], str]:
        """"從傳入的URL中去載入數據，返回LangChain文件列表或者字串"""
        # 1.下載遠程URL的文件到本地
        response = requests.get(url)

        # 2.將文件下載到本地的臨時文件夾
        with tempfile.TemporaryDirectory() as temp_dir:
            # 3.獲取文件的副檔名，並構建臨時儲存路徑，將遠程文件儲存到本地
            file_path = os.path.join(temp_dir, os.path.basename(url))
            with open(file_path, "wb") as file:
                file.write(response.content)

            return cls.load_from_file(file_path, return_text)

    @classmethod
    def load_from_file(
            cls,
            file_path: str,
            return_text: bool = False,
            is_unstructured: bool = True,
    ) -> Union[list[LCDocument], str]:
        """從本地文件中載入數據，返回LangChain文件列表或者字串"""
        # 1.獲取文件的副檔名
        delimiter = "\n\n"
        file_extension = Path(file_path).suffix.lower()

        # 2.根據不同的文件副檔名去載入不同的載入器
        if file_extension in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(file_path)
        elif file_extension == ".pdf":
            loader = UnstructuredPDFLoader(file_path)
        elif file_extension in [".md", ".markdown"]:
            loader = UnstructuredMarkdownLoader(file_path)
        elif file_extension in [".htm", ".html"]:
            loader = UnstructuredHTMLLoader(file_path)
        elif file_extension in [".png", ".jpg", ".jpeg"]:
            loader = UnstructuredImageLoader(file_path)
        elif file_extension == ".csv":
            loader = UnstructuredCSVLoader(file_path)
        elif file_extension in [".ppt", "pptx"]:
            loader = UnstructuredPowerPointLoader(file_path)
        elif file_extension == ".xml":
            loader = UnstructuredXMLLoader(file_path)
        else:
            loader = UnstructuredFileLoader(file_path) if is_unstructured else TextLoader(file_path)

        # 3.返回載入的文件列表或者文本
        return delimiter.join([document.page_content for document in loader.load()]) if return_text else loader.load()
