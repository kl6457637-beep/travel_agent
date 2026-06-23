"""
天气查询工具 — 调用中国天气网免费 API

中国天气网（weather.com.cn）提供实时天气查询，无需注册、无需 API Key。
"""

import requests
from langchain_core.tools import tool

# 城市名 → 中国天气网城市代码
CITY_IDS = {
    "北京": "101010100", "beijing": "101010100",
    "上海": "101020100", "shanghai": "101020100",
    "广州": "101280101", "guangzhou": "101280101",
    "深圳": "101280601", "shenzhen": "101280601",
    "杭州": "101210101", "hangzhou": "101210101",
    "成都": "101270101", "chengdu": "101270101",
    "南京": "101190101", "nanjing": "101190101",
    "武汉": "101200101", "wuhan": "101200101",
    "西安": "101110101", "xian": "101110101",
    "重庆": "101040100", "chongqing": "101040100",
    "厦门": "101230201", "xiamen": "101230201",
    "三亚": "101310201", "sanya": "101310201",
    "昆明": "101290101", "kunming": "101290101",
    "哈尔滨": "101050101", "haerbin": "101050101",
    "拉萨": "101140101", "lasa": "101140101",
    "乌鲁木齐": "101130101", "wulumuqi": "101130101",
    "苏州": "101190401", "suzhou": "101190401",
    "青岛": "101120201", "qingdao": "101120201",
    "大连": "101070201", "dalian": "101070201",
    "长沙": "101250101", "changsha": "101250101",
    "天津": "101030100", "tianjin": "101030100",
    "郑州": "101180101", "zhengzhou": "101180101",
    "济南": "101120101", "jinan": "101120101",
    "福州": "101230101", "fuzhou": "101230101",
    "贵阳": "101260101", "guiyang": "101260101",
    "南宁": "101300101", "nanning": "101300101",
    "海口": "101310101", "haikou": "101310101",
    "兰州": "101160101", "lanzhou": "101160101",
    "银川": "101170101", "yinchuan": "101170101",
    "合肥": "101220101", "hefei": "101220101",
    "南昌": "101240101", "nanchang": "101240101",
    "沈阳": "101070101", "shenyang": "101070101",
    "太原": "101100101", "taiyuan": "101100101",
    "长春": "101060101", "changchun": "101060101",
    "呼和浩特": "101080101", "huhehaote": "101080101",
    "石家庄": "101090101", "shijiazhuang": "101090101",
}

# 风力等级描述映射
WIND_LEVELS = {
    "1级": "微风",
    "2级": "轻风",
    "3级": "微风",
    "4级": "和风",
    "5级": "清风",
    "6级": "强风",
    "7级": "劲风",
    "8级": "大风",
    "9级": "烈风",
    "10级": "狂风",
}


@tool
def get_weather(city: str, date: str = "today") -> str:
    """查询指定城市在指定日期的天气状况。

    当用户询问某个城市的天气信息时必须调用此工具。

    Args:
        city: 城市名称，例如 "北京"、"上海"、"广州"
        date: 日期，默认为 "today" 表示今天

    Returns:
        天气描述字符串，包含天气状况、温度、风力等信息
    """
    try:
        # 查找城市代码
        city_id = CITY_IDS.get(city.lower() if city else "")
        if not city_id:
            # 列出支持的城市
            cities = sorted(set(k for k in CITY_IDS if not k.isascii()))
            return (
                f"暂不支持查询「{city}」的天气。"
                f"目前支持的城市：{', '.join(cities[:20])}等"
            )

        # 中国天气网实时天气 API — 完全免费
        url = f"https://www.weather.com.cn/data/sk/{city_id}.html"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        info = data["weatherinfo"]
        temp = info["temp"]
        wind_dir = info["WD"]  # 如 "东南风"
        wind_level = info["WS"]  # 如 "1级"
        humidity = info["SD"]  # 如 "17%"
        city_name = info["city"]
        rain = info.get("rain", "0")

        # 风力转可读描述
        wind_desc = WIND_LEVELS.get(wind_level, wind_level)

        result = (
            f"{city_name}当前温度{temp}°C，"
            f"{wind_dir}{wind_desc}，"
            f"相对湿度{humidity}"
        )
        if rain != "0":
            result += f"，降雨量{rain}mm"

        return result

    except requests.RequestException as e:
        return f"天气查询网络请求失败：{str(e)}"
    except (KeyError, IndexError) as e:
        return f"天气数据解析失败：{str(e)}，请稍后重试"
