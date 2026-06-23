# 智能旅行助手 — Web 前端设计文档

> 日期：2026-06-23
> 状态：待用户审阅

---

## 1. 项目概述

为已有的旅行助手 Agent 添加 Web 前端界面。原先 Agent 只能在命令行运行，现在通过 FastAPI + 内嵌 HTML 页面，让用户通过浏览器与 Agent 交互，并且可视化展示 Agent 的分步推理过程。

**核心理念：** 展示 Agent "如何思考"——用户不仅看到最终答案，还看到 Agent 每一步调用了什么工具、观察到了什么结果。

---

## 2. 架构设计

```
浏览器 (static/index.html)
    │  POST /api/chat  {"query": "..."}
    ▼
FastAPI (src/app.py)
    │  1. 加载 .env 配置
    │  2. 调用 create_travel_agent()
    │  3. agent.invoke({"messages": [...]})
    │  4. 解析 messages 列表 → 提取推理步骤 + 最终答案
    │  5. 返回 JSON
    ▼
LangChain Agent (已有的 src/agent.py + src/tools/)
    │  get_weather → 中国天气网 API
    │  recommend_spot → DeepSeek 推理
```

**不修改任何已有代码。** `agent.py`、`tools/` 完全不动，`app.py` 只是调用现有 `create_travel_agent()`。

---

## 3. 文件变更

```
travel-agent/
├── src/
│   ├── app.py              ← 新增：FastAPI 后端
│   └── static/
│       └── index.html      ← 新增：前端单页面
├── requirements.txt        ← 修改：增加 fastapi, uvicorn
├── (agent.py, tools/, main.py — 不动)
```

---

## 4. 后端设计（app.py）

### 4.1 API 端点

```
POST /api/chat
  Request:  {"query": "查询北京天气，推荐景点"}
  Response: {
    "steps": [
      {
        "round": 1,
        "thought": "先查天气",
        "tool": "get_weather",
        "tool_input": "{\"city\": \"北京\"}",
        "observation": "北京当前温度18°C，东南风1级..."
      },
      {
        "round": 2,
        "thought": "有天气了，推荐景点",
        "tool": "recommend_spot",
        "tool_input": "{\"city\": \"北京\", \"weather_info\": \"18°C，东南风...\"}",
        "observation": "推荐香山公园、故宫..."
      }
    ],
    "answer": "今天北京晴天18°C，为您推荐..."
  }
```

### 4.2 推理步骤提取逻辑

LangChain `agent.invoke()` 返回的 `messages` 列表包含所有中间消息。提取逻辑：

1. 遍历 `result["messages"]`
2. 如果 `AIMessage` 包含 `tool_calls`：记录 thought（content）和 tool 调用信息
3. 如果 `ToolMessage`：记录 observation
4. 最后一个 `AIMessage`（不含 tool_calls）：最终答案

### 4.3 静态文件

FastAPI 挂载 `static/` 目录，访问 `/` 直接返回 `index.html`。

---

## 5. 前端设计（index.html）

### 5.1 布局结构

```
┌─────────────────────────────────────────────┐
│  🌿 智能旅行助手         (薄荷绿渐变顶栏)       │
├─────────────────────────────────────────────┤
│                                             │
│  💬 用户消息气泡（右对齐，绿色底）              │
│                                             │
│  📊 Agent 推理链（可折叠卡片）                 │
│   ┌─ 🔄 Round 1 ──────────────────────────┐ │
│   │  💭 思考：先查询天气                   │ │
│   │  🔧 工具：get_weather("北京")          │ │
│   │  📊 结果：晴, 18°C, 微风               │ │
│   └───────────────────────────────────────┘ │
│   ┌─ 🔄 Round 2 ──────────────────────────┐ │
│   │  💭 思考：推荐景点                    │ │
│   │  🔧 工具：recommend_spot(...)          │ │
│   │  📊 结果：香山公园、故宫...             │ │
│   └───────────────────────────────────────┘ │
│                                             │
│  🌍 最终回答气泡（左对齐，淡蓝底）             │
│                                             │
├─────────────────────────────────────────────┤
│  [🔍 请输入问题...]              [✈️ 发送]   │
└─────────────────────────────────────────────┘
```

### 5.2 配色方案（自然清新风）

| 元素 | 颜色 |
|---|---|
| 顶栏背景 | 渐变 `#43A047` → `#1E88E5` |
| 用户气泡 | `#E8F5E9` + 边框 `#A5D6A7` |
| 推理卡片 | 左边框 `#43A047` + 背景 `#F1F8E9` |
| 回答气泡 | `#E3F2FD` + 边框 `#90CAF9` |
| 发送按钮 | `#43A047`（绿色） |

### 5.3 交互行为

- 输入回车或点击发送按钮提交
- 发送后显示 loading 状态："Agent 思考中..."
- 收到响应后：渲染推理链卡片 + 最终回答
- 推理链可点击折叠/展开
- 自动滚动到最新消息

### 5.4 技术约束

- 纯 HTML + CSS + 原生 JS，零前端框架
- 所有内容通过 `fetch()` 调用后端
- 单文件，无构建步骤

---

## 6. 依赖变更

`requirements.txt` 增加：
```
fastapi>=0.115.0
uvicorn>=0.34.0
```

---

## 7. 运行方式

```bash
cd travel-agent
uvicorn src.app:app --reload --port 8000
```

浏览器打开 http://localhost:8000

---

## 8. 不做（YAGNI）

- 不做多轮对话历史（页面刷新后清空）
- 不做 SSE 流式传输（先返回完整结果）
- 不做移动端适配
- 不做暗色模式
- 不做登录/用户系统

---

## 9. 验收标准

1. 浏览器打开 `localhost:8000` 看到旅行助手界面
2. 输入"查询今天北京天气，推荐景点"，点击发送
3. 推理链显示 2 轮步骤（get_weather → recommend_spot）
4. 最终回答包含具体景点和推荐理由
5. 界面配色为薄荷绿+天空蓝清新风格
6. 推理链卡片可折叠
