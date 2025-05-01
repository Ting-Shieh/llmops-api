#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/13 下午7:05
@Author : zsting29@gmail.com
@File   : WeatherTool.py
"""
import json
import os
from typing import Any, Type

import dotenv
import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

dotenv.load_dotenv()


class WeatherToolArgsSchema(BaseModel):
    city: str = Field(description="需要查詢天氣預報的目標城市，例如：高雄")


class GoogleWeatherTool(BaseTool):
    """search weather from input city"""
    name: str = "google_weather"
    description: str = "當你想查詢天氣或與天氣相關問題時可以使用的工具"
    args_schema: Type[BaseModel] = WeatherToolArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """根據傳入城市名稱運行調用API獲取城市對應的天氣預報信息"""
        try:
            # 1.地名轉經緯度google key ，假如沒有創建，則拋出錯誤
            google_api_key = os.getenv("GOOGLE_WEATHER_API_KEY")
            if not google_api_key:
                return f"Google Weather API 未配置"
            # 2.從參數中獲取city名
            city = kwargs.get("city", "")
            maps_api_domain = "https://maps.googleapis.com"
            weather_api_domain = "https://weather.googleapis.com"
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
            if city_geo_data.get("status") == "OK":
                location = city_geo_data.get("results")[0]["geometry"]["location"]
                # 4.依據lat, lng調用天氣預報API，獲取天氣訊息
                weather_response = session.request(
                    method="GET",
                    url=f"{weather_api_domain}/v1/currentConditions:lookup?key={google_api_key}&location.latitude={location["lat"]}&location.longitude={location["lng"]}&unitsSystem=METRIC",
                    headers={
                        "Content-Type": "application/json; charset=UTF-8",
                    }
                )

                weather_response.raise_for_status()
                weather_data = weather_response.json()
                # 5.返回最後結果字符串
                return json.dumps(weather_data)
            return f"獲取{city}天氣預報訊息失敗"
        except Exception as e:
            return f"獲取{kwargs.get('city', '')}天氣預報訊息失敗"


google_weather = GoogleWeatherTool()
# print(google_weather.invoke({"city": "台北"}))
