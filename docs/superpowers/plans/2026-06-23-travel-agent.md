# 智能旅行助手 Agent — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于 LangChain + DeepSeek 的分步推理旅行助手 Agent，能先查天气再推荐景点。

**Architecture:** LangChain `create_tool_calling_agent` + `AgentExecutor` 循环驱动。两个工具：`get_weather`（调取和风天气 API）、`recommend_spot`（内部调用 LLM 推理推荐）。命令行交互，verbose 输出完整决策链。

**Tech Stack:** Python 3.10+, LangChain >= 0.3.0, langchain-openai >= 0.2.0, DeepSeek API (deepseek-chat), 和风天气免费 API, requests, python-dotenv

**File Map (9 个文件，3 个模块):**

| 文件 | 职责 |
|---|---|
| `travel-agent/src/__init__.py` | src 包初始化 — 使 `from src.xxx` 导入生效 |
| `travel-agent/src/tools/__init__.py` | 工具包导出 |
| `travel-agent/src/tools/weather.py` | `get_weather` 工具 — 封装和风天气 API |
| `travel-agent/src/tools/spot.py` | `recommend_spot` 工具 — 内部调 LLM 推理推荐 |
| `travel-agent/src/agent.py` | LangChain Agent 创建 — LLM 配置 + 工具注册 + AgentExecutor |
| `travel-agent/src/main.py` | CLI 入口 — 加载配置 + 接收输入 + 运行 Agent |
| `travel-agent/requirements.txt` | Python 依赖声明 |
| `travel-agent/.env.example` | API Key 配置模板 |
| `travel-agent/.gitignore` | 忽略 .env 等敏感文件 |

---

### Task 1: 项目脚手架

**产出:** 目录结构、依赖文件、配置模板、.gitignore

**Files:**
- Create: `travel-agent/src/__init__.py`
- Create: `travel-agent/requirements.txt`
- Create: `travel-agent/.env.example`
- Create: `travel-agent/.gitignore`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p travel-agent/src/tools
```

- [ ] **Step 2: 写 src/__init__.py**

```python
"""智能旅行助手 Agent — src 包"""
```

- [ ] **Step 3: 写 requirements.txt**

```txt
langchain>=0.3.0
langchain-openai>=0.2.0
requests>=2.32.0
python-dotenv>=1.0.0
```

- [ ] **Step 4: 写 .env.example**

```
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
QWEATHER_API_KEY=your-qweather-api-key
```

- [ ] **Step 5: 写 .gitignore**

```
.env
__pycache__/
*.pyc
.venv/
venv/
```

- [ ] **Step 6: 安装依赖**

```bash
cd travel-agent
pip install -r requirements.txt
```

Expected: 所有 4 个包安装成功，无报错。

- [ ] **Step 7: Commit**

```bash
git add travel-agent/requirements.txt travel-agent/.env.example travel-agent/.gitignore
git commit -m "chore: add project scaffolding for travel agent"
```

---

### Task 2: 天气查询工具 `get_weather`

**产出:** `src/tools/__init__.py` + `src/tools/weather.py`，包含完整的 `get_weather` LangChain Tool

**Files:**
- Create: `travel-agent/src/tools/__init__.py`
- Create: `travel-agent/src/tools/weather.py`

- [ ] **Step 1: 写 `__init__.py`**

`travel-agent/src/tools/__init__.py`:
```python
"""旅行助手 Agent 工具集"""

from .weather import get_weather
from .spot import recommend_spot

__all__ = ["get_weather", "recommend_spot"]
```

- [ ] **Step 2: 写 weather.py**

`travel-agent/src/tools/weather.py`:
```python
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
```

**代码含义说明：**
- `@tool` 装饰器将普通函数注册为 LangChain Tool，框架自动从 docstring 提取工具描述
- 和风天气 API 两步走：先城市搜索拿 `location_id`，再用 `location_id` 查天气
- 每次 API 调用都有 try/except 兜底，所有错误返回字符串而不是抛异常（Agent 看到错误信息可以自行调整）
- 返回值是自然语言字符串，方便 Agent 和李安用户理解

- [ ] **Step 3: 验证工具可导入**

```bash
cd travel-agent
python -c "from src.tools.weather import get_weather; print(type(get_weather))"
```

Expected: 输出 `<class 'langchain_core.tools.base.BaseTool'>`（LangChain Tool 类型）

- [ ] **Step 4: Commit**

```bash
git add travel-agent/src/tools/__init__.py travel-agent/src/tools/weather.py
git commit -m "feat: add get_weather tool with HeFeng weather API"
```

---

### Task 3: 景点推荐工具 `recommend_spot`

**产出:** `src/tools/spot.py`，包含 `recommend_spot` 工具（内部调用 LLM 推理）

**Files:**
- Create: `travel-agent/src/tools/spot.py`

- [ ] **Step 1: 写 spot.py**

`travel-agent/src/tools/spot.py`:
```python
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
```

**代码含义说明：**
- `_get_llm_for_recommendation()` 是模块内部函数（下划线开头），创建独立的 LLM 连接
- temperature=0.8 比默认值高，让推荐更多样化（晴天不会每次都推故宫）
- 工具内部调用 LLM 是合理设计——景点推荐需要"知识+推理"，没有现成 API 能替代
- prompt 中给出了明确的输出格式要求，确保 Agent 拿到结构化推荐文本

- [ ] **Step 2: 验证工具可导入**

```bash
cd travel-agent
python -c "from src.tools.spot import recommend_spot; print(type(recommend_spot))"
```

Expected: 输出 `<class 'langchain_core.tools.base.BaseTool'>`

- [ ] **Step 3: Commit**

```bash
git add travel-agent/src/tools/spot.py
git commit -m "feat: add recommend_spot tool with LLM-powered reasoning"
```

---

### Task 4: Agent 核心 — LLM 配置 + 工具注册 + AgentExecutor

**产出:** `src/agent.py`，创建并返回一个可用的 Agent

**Files:**
- Create: `travel-agent/src/agent.py`

- [ ] **Step 1: 写 agent.py**

`travel-agent/src/agent.py`:
```python
"""
Agent 核心模块 — 配置 LLM、注册工具、创建 AgentExecutor

基于 LangChain 的 create_tool_calling_agent 创建 Agent。
Agent 用 function calling 机制决定何时调用哪个工具。
AgentExecutor 负责执行 Agent 循环：
  LLM 思考 → 输出工具调用 → 执行工具 → 观察结果 → 再思考 → ... → Final Answer
"""

import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .tools import get_weather, recommend_spot


def create_agent() -> AgentExecutor:
    """创建旅行助手 Agent，返回可执行的 AgentExecutor。

    Returns:
        AgentExecutor: 配置好的 Agent 执行器，调用 .invoke({"input": "..."}) 即可运行
    """

    # ── 1. 配置 LLM ──────────────────────────────────
    # ChatOpenAI 兼容 OpenAI SDK 协议，因此可以直接对接 DeepSeek
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=0.7,  # 主 Agent 用 0.7 平衡推理准确性和多样性
    )

    # ── 2. 注册工具列表 ──────────────────────────────
    # Agent 会在运行时根据用户问题，自主决定调用哪个工具
    tools = [get_weather, recommend_spot]

    # ── 3. 构建 Prompt 模板 ──────────────────────────
    # System Prompt 定义 Agent 的行为规则
    # MessagesPlaceholder 用于注入 Agent 的思考历史和工具调用记录
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是一个智能旅行助手。你的任务是帮助用户查询天气并推荐旅游景点。

工作流程：
1. 如果用户提到了天气相关的问题，先调用 get_weather 工具获取天气数据
2. 拿到天气数据后，再调用 recommend_spot 工具推荐合适的景点
3. 最后综合所有信息，给用户一个完整、友好的回答

规则：
- 必须按照"先天气，后推荐"的顺序操作，不要跳过任何一步
- 回答时使用中文
- 回答要具体，包含景点名称、推荐理由和出行建议""",
            ),
            ("user", "{input}"),
            # agent_scratchpad 由 AgentExecutor 自动填充：存放 Agent 的思考链和工具调用记录
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # ── 4. 创建 Agent ─────────────────────────────────
    # create_tool_calling_agent 会将工具的定义（名称、参数、描述）注入 LLM
    # LLM 通过 function calling 输出 tool_calls，而非直接回答
    agent = create_tool_calling_agent(llm, tools, prompt)

    # ── 5. 创建 AgentExecutor ─────────────────────────
    # AgentExecutor 负责执行 Agent 循环：
    #   调用 LLM → 解析 tool_calls → 执行工具 → 把结果喂回 LLM → 继续循环 → 直到输出 Final Answer
    # verbose=True 会在控制台打印完整的思考链和工具调用过程
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,           # 打印 Thought → Action → Observation
        handle_parsing_errors=True,  # LLM 输出格式出错时自动重试
        max_iterations=10,      # 最多循环 10 轮，避免死循环
    )

    return executor
```

**代码含义说明：**
- `ChatOpenAI(base_url=...)` — DeepSeek 兼容 OpenAI SDK 协议，只需替换 base_url 即可
- `create_tool_calling_agent` — 把 tool 的函数签名和 docstring 转成 LLM 能理解的 function schema，内置在 prompt 中
- `MessagesPlaceholder(variable_name="agent_scratchpad")` — 占位符，AgentExecutor 自动往里填"上一轮的思考+工具调用结果"
- `handle_parsing_errors=True` — 如果 LLM 输出的 JSON 格式有误，自动把错误信息喂回去让它重试
- `max_iterations=10` — 安全阀，防止 Agent 陷入循环（正常只需 2-3 轮）

- [ ] **Step 2: 验证 Agent 创建（不实际调用 LLM — 只测创建成功）**

```bash
cd travel-agent
python -c "
import os
os.environ['DEEPSEEK_API_KEY'] = 'sk-fake-for-test'
from src.agent import create_agent
agent = create_agent()
print('Agent 类型:', type(agent).__name__)
print('已注册工具:', [t.name for t in agent.tools])
"
```

Expected 输出:
```
Agent 类型: AgentExecutor
已注册工具: ['get_weather', 'recommend_spot']
```

- [ ] **Step 3: Commit**

```bash
git add travel-agent/src/agent.py
git commit -m "feat: add agent core with LangChain AgentExecutor"
```

---

### Task 5: CLI 入口 `main.py`

**产出:** `src/main.py`，命令行交互入口

**Files:**
- Create: `travel-agent/src/main.py`

- [ ] **Step 1: 写 main.py**

`travel-agent/src/main.py`:
```python
"""
旅行助手 Agent — 命令行入口

用法：
    cd travel-agent
    python -m src.main

使用前请将 .env.example 复制为 .env 并填入真实的 API Key：
    DEEPSEEK_API_KEY=sk-your-key
    QWEATHER_API_KEY=your-key
"""

import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量（必须在导入 agent 之前加载）
load_dotenv()

from src.agent import create_agent


def check_env() -> bool:
    """检查必要的环境变量是否已配置"""
    missing = []
    if not os.getenv("DEEPSEEK_API_KEY"):
        missing.append("DEEPSEEK_API_KEY")
    if not os.getenv("QWEATHER_API_KEY"):
        missing.append("QWEATHER_API_KEY")

    if missing:
        print("=" * 60)
        print("❌ 缺少以下环境变量配置：")
        for key in missing:
            print(f"   - {key}")
        print()
        print("请将 .env.example 复制为 .env 并填入真实的 API Key")
        print("=" * 60)
        return False
    return True


def main():
    """主函数：创建 Agent，接收用户输入，运行 Agent"""
    print("=" * 60)
    print("🧳  智能旅行助手 Agent")
    print("=" * 60)
    print("提示：输入 'exit' 或 'quit' 退出")
    print()

    if not check_env():
        sys.exit(1)

    print("✅ 环境配置检查通过，正在初始化 Agent...")
    agent = create_agent()
    print("✅ Agent 就绪！")
    print()

    # ── 交互循环 ──────────────────────────────────
    while True:
        try:
            user_input = input("👤 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("👋 再见！")
            break

        print("\n" + "─" * 60)
        print("🤖 Agent 思考中...\n")

        try:
            # invoke 触发 Agent 执行循环
            # verbose=True（在 agent.py 中配置）会在控制台打印每一步
            result = agent.invoke({"input": user_input})
            print("\n" + "─" * 60)
            print("📋 最终回答：")
            print(result["output"])
            print("─" * 60 + "\n")

        except Exception as e:
            print(f"\n❌ Agent 运行出错：{e}\n")


if __name__ == "__main__":
    main()
```

**代码含义说明：**
- `load_dotenv()` 必须在导入 agent 之前调用，因为 `create_agent()` 就要读取环境变量
- `check_env()` 提前验证配置，给出友好提示而不是让 Agent 运行时莫名其妙报错
- `agent.invoke({"input": user_input})` — 一行代码触发完整的 Agent 循环，返回包含 `output` 的字典
- try/except 捕获 `EOFError`（Ctrl+D）和 `KeyboardInterrupt`（Ctrl+C），优雅退出

- [ ] **Step 2: 验证 CLI 启动（配置检查失败场景）**

```bash
cd travel-agent
python -c "
from dotenv import load_dotenv
load_dotenv()
import os
# 临时清空环境变量以测试配置检查
os.environ.pop('DEEPSEEK_API_KEY', None)
os.environ.pop('QWEATHER_API_KEY', None)
from src.main import check_env
result = check_env()
assert result == False, '应该返回 False'
print('配置检查逻辑正常')
"
```

Expected: `配置检查逻辑正常`

- [ ] **Step 3: Commit**

```bash
git add travel-agent/src/main.py
git commit -m "feat: add CLI entry with env check and interactive loop"
```

---

### Task 6: 端到端集成验证

**产出:** 确认 Agent 完整可用，分步推理链正确

**Files:** 无新文件，验证已有代码

- [ ] **Step 1: 创建 .env 文件并填入真实 API Key**

将 `travel-agent/.env.example` 复制为 `travel-agent/.env`，填入：
```
DEEPSEEK_API_KEY=sk-你的真实key
DEEPSEEK_BASE_URL=https://api.deepseek.com
QWEATHER_API_KEY=你的和风天气key
```

- [ ] **Step 2: 运行端到端测试**

```bash
cd travel-agent
python -m src.main
```

输入:
```
请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。
```

- [ ] **Step 3: 验证输出满足验收标准**

逐项检查：

| 检查项 | 标准 |
|---|---|
| ✅ Agent 调用了 `get_weather` | verbose 输出中出现 `get_weather` 工具调用 |
| ✅ Agent 调用了 `recommend_spot` | verbose 输出中出现 `recommend_spot` 工具调用 |
| ✅ 调用顺序正确 | `get_weather` 在 `recommend_spot` 之前 |
| ✅ 天气数据真实 | 温度、天气状况与和风天气 API 返回一致 |
| ✅ 推荐包含具体景点 | 输出中有 3+ 个景点名称和推荐理由 |
| ✅ 中文输出 | 最终回答使用中文 |

- [ ] **Step 4: 测试错误处理 — 缺少 API Key 的场景**

```bash
cd travel-agent
# 临时移除 API Key 测试错误提示
set QWEATHER_API_KEY=
python -c "
from dotenv import load_dotenv
load_dotenv()
import os
os.environ.pop('QWEATHER_API_KEY', None)
from src.tools.weather import get_weather
result = get_weather.invoke({'city': '北京', 'date': 'today'})
print(result)
assert '未配置' in result
print('✅ 错误处理正常')
"
```

Expected: 输出包含 `未配置和风天气 API Key`，不抛异常。

- [ ] **Step 5: Commit（如有 .env 之外的变更）**

```bash
git status
# 确认 .env 在 .gitignore 中，不会被提交
```
