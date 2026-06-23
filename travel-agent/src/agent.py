"""
Agent 核心模块 — 配置 LLM、注册工具、创建 Agent

基于 LangChain 1.3 的 create_agent 创建 Agent。
Agent 用 function calling 机制决定何时调用哪个工具。
create_agent 返回一个 CompiledStateGraph，内部实现 Agent 循环：
  LLM 思考 → 输出工具调用 → 执行工具 → 观察结果 → 再思考 → ... → Final Answer
"""

import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from .tools import get_weather, recommend_spot


def create_travel_agent(debug: bool = False):
    """创建旅行助手 Agent，返回编译好的 StateGraph。

    LangChain 1.3 中 create_agent 替代了旧版的：
    - create_tool_calling_agent（创建 agent runnable）
    - AgentExecutor（执行 Agent 循环）

    现在这俩角色合二为一，create_agent 直接返回一个可执行的图。

    Args:
        debug: 是否打印 Agent 每一步的执行细节。CLI 模式建议 True，Web 模式必须 False

    Returns:
        CompiledStateGraph: 编译好的 Agent 图，调用 .invoke({"messages": [...]}) 即可运行
    """

    # ── 1. 配置 LLM ──────────────────────────────────
    # ChatOpenAI 兼容 OpenAI SDK 协议，因此可以直接对接 DeepSeek
    # model 参数可以传字符串也可以传 ChatModel 实例
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=0.7,  # 主 Agent 用 0.7 平衡推理准确性和多样性
    )

    # ── 2. 注册工具列表 ──────────────────────────────
    # Agent 会在运行时根据用户问题，自主决定调用哪个工具
    tools = [get_weather, recommend_spot]

    # ── 3. 定义 System Prompt ────────────────────────
    # LangChain 1.3 直接传字符串，不需要 ChatPromptTemplate
    system_prompt = """你是一个智能旅行助手。你的任务是帮助用户查询天气并推荐旅游景点。

工作流程：
1. 如果用户提到了天气相关的问题，先调用 get_weather 工具获取天气数据
2. 拿到天气数据后，再调用 recommend_spot 工具推荐合适的景点
3. 最后综合所有信息，给用户一个完整、友好的回答

规则：
- 必须按照"先天气，后推荐"的顺序操作，不要跳过任何一步
- 回答时使用中文
- 回答要具体，包含景点名称、推荐理由和出行建议"""

    # ── 4. 创建 Agent ─────────────────────────────────
    # create_agent 直接将工具定义（名称、参数、描述）注入 LLM
    # LLM 通过 function calling 输出 tool_calls，而非直接回答
    # 内部是一个 StateGraph：model node → tools node → model node → ... → end
    # debug=True 会在控制台打印完整的思考链和工具调用过程
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        debug=debug,  # Web 模式关掉避免 GBK 编码问题
    )

    return agent
