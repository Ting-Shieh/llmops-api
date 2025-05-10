#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/8 下午9:07
@Author : zsting29@gmail.com
@File   : google_lnglat.py
"""
import json
import os
from typing import Any, Type

import requests
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


class LngLatToolArgsSchema(BaseModel):
    city: str = Field(description="查詢目標城市的地理位置資訊")


class GoogleGeoTool(BaseTool):
    """search weather from input city"""
    name: str = "google_lnglat"
    description: str = "查詢目標城市的地理位置資訊"
    args_schema: Type[BaseModel] = LngLatToolArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """根據傳入城市名稱運行調用API獲取城市對應的地理位置資訊"""
        try:
            # 1.地名轉經緯度google key ，假如沒有創建，則拋出錯誤
            google_api_key = os.getenv("GOOGLE_WEATHER_API_KEY")
            if not google_api_key:
                return f"Google API 未配置"
            # 2.從參數中獲取city名
            city = kwargs.get("city", "")
            maps_api_domain = "https://maps.googleapis.com"
            session = requests.session()
            # 3.發起地名轉經緯度查詢（lat, lng）
            city_res = session.request(
                method="GET",
                url=f"{maps_api_domain}/maps/api/geocode/json?address={city}&key={google_api_key}",
                headers={
                    "Content-Type": "application/json; charset=UTF-8",
                }
            )
            city_res.raise_for_status()
            city_geo_data = city_res.json()
            return json.dumps(city_geo_data)
        except Exception as e:
            return f"獲取{kwargs.get('city', '')}地理位置資訊失敗"


@add_attribute("args_schema", LngLatToolArgsSchema)
def google_lnglat(**kwargs) -> BaseTool:
    """獲取Google Map地理位置工具"""
    return GoogleGeoTool()
