# 🌿 智能旅行助手 Agent

一个基于 **LangChain + DeepSeek** 的多步推理旅行助手。Agent 自主规划工具调用顺序：先查天气 → 再推景点 → 输出建议。展示完整的 **Thought → Action → Observation** 推理链。

**🎯 核心亮点：不是简单的 Chatbot，而是能分步决策、自主调用工具的 AI Agent。**

---

## ✨ 功能

- 🔄 **分步推理** — Agent 先调用天气工具获取数据，再基于天气调用推荐工具
- 🧠 **推理可视化** — Web 界面实时展示每一步：思考 → 工具调用 → 观察结果
- 🌤️ **真实天气** — 接入中国天气网 API，实时天气数据（免费，无需 Key）
- 🏯 **智能推荐** — DeepSeek 根据天气状况推理推荐景点，附带理由和出行建议
- 💻 **双模式运行** — Web 界面（FastAPI） 和命令行（CLI） 两种方式

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd travel-agent
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
# DEEPSEEK_API_KEY=sk-你的key
```

> 申请 DeepSeek API Key：https://platform.deepseek.com

### 3. 运行

**Web 界面（推荐）：**

```bash
uvicorn src.app:app --port 8000
# 浏览器打开 http://localhost:8000
```

**命令行：**

```bash
python -m src.main
```

### 4. 试试这个

```
请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。
```

Agent 会自动：
1. 调用 `get_weather` → 获取北京实时温度、风力、湿度
2. 调用 `recommend_spot` → 根据天气推荐景点
3. 输出结构化回答，附带出行建议

---

## 🏗️ 架构

```
用户输入
   │
   ▼
┌─────────────┐     ┌──────────────────┐
│  Web 界面    │────▶│  FastAPI 后端     │
│  index.html │     │  POST /api/chat  │
└─────────────┘     └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  LangChain Agent  │
                    │  create_agent()   │
                    └──┬──────────┬────┘
                       │          │
              ┌────────▼──┐  ┌───▼──────────┐
              │ get_weather│  │ recommend_spot│
              │ 中国天气网  │  │ DeepSeek 推理  │
              └────────────┘  └──────────────┘
```

## 📁 项目结构

```
travel-agent/
├── src/
│   ├── app.py              # FastAPI Web 后端
│   ├── agent.py            # LangChain Agent 核心
│   ├── main.py             # CLI 命令行入口
│   ├── static/
│   │   └── index.html      # Web 聊天界面
│   └── tools/
│       ├── weather.py      # 天气查询工具
│       └── spot.py         # 景点推荐工具
├── .env.example            # 配置模板
├── requirements.txt
└── README.md
```

---

## 🛠 技术栈

| 组件 | 技术 |
|---|---|
| Agent 框架 | LangChain 1.3 (create_agent) |
| LLM | DeepSeek (deepseek-chat) |
| Web 后端 | FastAPI + uvicorn |
| Web 前端 | 纯 HTML/CSS/JS（零框架） |
| 天气数据 | 中国天气网免费 API |
| Python | 3.10+ |

---

## 📄 许可

MIT
