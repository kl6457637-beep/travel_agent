"""
景点推荐工具 — 基于天气信息调用 LLM 推理推荐景点

与 get_weather 不同，此工具的数据来源不是外部 API，
而是利用 DeepSeek 的推理能力，根据天气状况推荐合适的旅游景点。
"""

import os
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


def _get_llm_for_recommendation():
    """创建用于景点推荐的 LLM 实例"""
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=0.8,  # 推荐类任务给更高温度以增加多样性
    )


@tool
def recommend_spot(city: str, weather_info: str) -> str:
    """根据城市和天气信息推荐合适的旅游景点。

    当已有天气数据、需要为某个城市推荐景点时必须调用此工具。

    Args:
        city: 城市名称，例如 "北京"
        weather_info: 天气信息描述，例如 "晴天，22°C，微风"

    Returns:
        景点推荐文本，包含 3-4 个景点名称和推荐理由
    """
    if not os.getenv("DEEPSEEK_API_KEY"):
        return "错误：未配置 DeepSeek API Key，请设置环境变量 DEEPSEEK_API_KEY"

    try:
        llm = _get_llm_for_recommendation()

        prompt = f"""你是一位资深导游。请根据以下天气信息，为{city}推荐 3 个最合适的旅游景点。

天气信息：{weather_info}

要求：
- 每个景点给出名称和 1-2 句推荐理由（结合天气说明为什么推荐）
- 推荐应覆盖室内和室外景点，给用户多种选择
- 如果有特殊提醒（如带伞、防晒、保暖），请在最后注明

输出格式：
1. **景点名** — 推荐理由
2. **景点名** — 推荐理由
3. **景点名** — 推荐理由
💡 出行建议：..."""

        response = llm.invoke(prompt)
        return response.content

    except Exception as e:
        return f"景点推荐生成失败：{str(e)}"
