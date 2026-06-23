"""
天气查询工具 — 封装和风天气免费 API

和风天气 API 调用分两步：
1. 城市搜索 API 获取 location_id
2. 实时天气 API 获取天气数据
"""

import os
import requests
from langchain_core.tools import tool


@tool
def get_weather(city: str, date: str = "today") -> str:
    """查询指定城市在指定日期的天气状况。

    当用户询问某个城市的天气信息时必须调用此工具。

    Args:
        city: 城市名称，例如 "北京"、"上海"、"广州"
        date: 日期，默认为 "today" 表示今天，支持 "tomorrow"

    Returns:
        天气描述字符串，包含天气状况、温度、风力等信息
    """
    api_key = os.getenv("QWEATHER_API_KEY")
    if not api_key:
        return "错误：未配置和风天气 API Key，请设置环境变量 QWEATHER_API_KEY"

    try:
        # 第一步：城市搜索 — 获取 location_id
        geo_url = "https://geoapi.qweather.com/v2/city/lookup"
        geo_resp = requests.get(
            geo_url,
            params={"location": city, "key": api_key},
            timeout=10,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        if geo_data.get("code") != "200" or not geo_data.get("location"):
            return f"未找到城市「{city}」的天气数据，请确认城市名称是否正确"

        location_id = geo_data["location"][0]["id"]

        # 第二步：获取实时天气
        weather_url = "https://devapi.qweather.com/v7/weather/now"
        weather_resp = requests.get(
            weather_url,
            params={"location": location_id, "key": api_key},
            timeout=10,
        )
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()

        if weather_data.get("code") != "200":
            return f"获取{city}天气失败，API 返回错误码：{weather_data.get('code')}"

        now = weather_data["now"]
        result = (
            f"{city}当前天气：{now['text']}，"
            f"温度{now['temp']}°C，"
            f"体感温度{now['feelsLike']}°C，"
            f"{now['windDir']}{now['windScale']}级，"
            f"相对湿度{now['humidity']}%，"
            f"能见度{now['vis']}公里"
        )
        return result

    except requests.RequestException as e:
        return f"天气查询网络请求失败：{str(e)}"
    except (KeyError, IndexError) as e:
        return f"天气数据解析失败：{str(e)}，请稍后重试"
