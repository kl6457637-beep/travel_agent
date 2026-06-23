# 智能旅行助手 Agent — 设计文档

> 日期：2026-06-23
> 状态：设计中 → 待用户审阅

---

## 1. 项目概述

构建一个能处理分步任务的智能旅行助手 Agent。用户输入自然语言请求，Agent 自主规划工具调用顺序，分步执行并综合结果输出建议。

**典型用例：** "请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"

**核心理念：** 展示 Agent 的分步决策能力——先查天气→再根据结果推荐景点→最终输出。

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────┐
│                    main.py                       │
│            (入口：接收用户问题，启动 Agent)          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│                  agent.py                        │
│   AgentExecutor ←  Agent(LLM + Tools)            │
│                                                   │
│   LLM 思考 → 选择工具 → 执行 → 观察结果 → 再思考...   │
└──────┬──────────────────────────┬───────────────┘
       │                          │
┌──────▼──────┐          ┌───────▼───────┐
│ get_weather │          │ recommend_spot │
│  (工具1)     │          │   (工具2)      │
└──────┬──────┘          └───────┬───────┘
       │                         │
┌──────▼──────┐          ┌───────▼───────┐
│  和风天气API  │          │  LLM 自主推理  │
│  真实天气数据  │          │  基于天气推荐   │
└─────────────┘          └───────────────┘
```

---

## 3. 文件结构

```
travel-agent/
├── src/
│   ├── main.py          # 入口，命令行交互界面
│   ├── agent.py         # LangChain Agent 配置与创建
│   └── tools/
│       ├── __init__.py
│       ├── weather.py   # get_weather 工具
│       └── spot.py      # recommend_spot 工具
├── .env                 # API Key 配置（不提交到 git）
├── .env.example         # API Key 配置模板
├── .gitignore
├── requirements.txt     # 依赖列表
└── README.md
```

---

## 4. 核心组件

### 4.1 LLM 层（agent.py）

- 使用 `ChatOpenAI`（兼容 OpenAI SDK）连接 DeepSeek API
- 模型：`deepseek-chat`
- 配置 temperature=0.7，确保推荐有一定多样性

### 4.2 工具层

| 工具 | 功能 | 输入 | 输出 | 数据来源 |
|---|---|---|---|---|
| `get_weather` | 查询城市天气 | city, date | 天气状况、温度、风力等 | 和风天气免费 API |
| `recommend_spot` | 根据天气推荐景点 | city, weather_info | 景点名称 + 推荐理由 | 工具内部调用 LLM 推理（复用 DeepSeek） |

### 4.3 Agent 层

- 使用 LangChain 的 `create_tool_calling_agent` 创建 Agent
- 使用 `AgentExecutor` 执行 Agent 循环
- 开启 `verbose=True` 打印决策链

---

## 5. Agent 执行流程

```
用户输入: "查询今天北京天气，推荐景点"

第 1 轮 ──────────────────────────
  Thought: 用户需要北京今天的天气，我先调用 get_weather
  Action: get_weather(city="北京", date="today")
  Observation: {"weather": "晴", "temp": "22°C", "wind": "微风"}

第 2 轮 ──────────────────────────
  Thought: 天气晴朗，温度舒适，适合户外活动。我需要推荐景点
  Action: recommend_spot(city="北京", weather="晴，22°C，微风")
  Observation: "推荐故宫、景山公园、798艺术区，理由：..."

最终输出 ──────────────────────────
  Final Answer: "今天北京晴天22°C，非常适合户外活动！
               为您推荐以下景点：
               1. 故宫博物院——晴天下红墙金瓦拍照最美
               2. 景山公园——登顶俯瞰故宫全景
               3. 798艺术区——下午逛逛文艺街区正合适"
```

---

## 6. API 依赖

| API | 用途 | 免费额度 | 申请地址 |
|---|---|---|---|
| DeepSeek API | LLM 推理 | 赠送额度 | platform.deepseek.com |
| 和风天气 API | 天气查询 | 1000次/天 | dev.qweather.com |

---

## 7. 依赖项（requirements.txt）

```
langchain>=0.3.0
langchain-openai>=0.2.0
requests>=2.32.0
python-dotenv>=1.0.0
```

---

## 8. 环境变量（.env）

```
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
QWEATHER_API_KEY=xxx
```

---

## 9. 非功能需求

- **可观测性：** 每一步打印 Thought / Action / Observation，完整展示推理链
- **错误处理：** API 调用失败时给出友好提示，不崩溃
- **可扩展性：** 新增工具只需在 tools/ 目录添加文件，在 agent.py 注册即可

---

## 10. 不做（YAGNI）

- 不做 Web 界面，先用命令行
- 不接旅游 POI 数据 API，景点推荐用 LLM 推理
- 不做多轮对话记忆，先做单轮分步任务
- 不做前端，纯后端 Agent

---

## 11. 验收标准

1. 输入"查询今天北京天气，推荐景点"，Agent 先调天气工具再调推荐工具
2. 天气数据来自和风天气真实 API（不是 mock）
3. 控制台输出每一步决策过程（Thought → Action → Observation）
4. 最终输出包含具体景点名称和推荐理由
