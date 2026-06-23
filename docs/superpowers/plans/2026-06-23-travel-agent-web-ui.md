# 智能旅行助手 Web 前端 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为已有旅行助手 Agent 添加 FastAPI + 静态 HTML 的 Web 前端，可视化展示 Agent 分步推理过程。

**Architecture:** FastAPI 单文件 (`app.py`) 提供 `POST /api/chat` 端点，调用 `create_travel_agent()` 运行 Agent，解析消息链提取推理步骤，返回 JSON。前端纯 HTML+CSS+JS 单文件 (`index.html`)，fetch 调用后端 API，自然清新风配色，推理链可折叠展示。

**Tech Stack:** FastAPI >= 0.115.0, uvicorn >= 0.34.0, 已有 LangChain 1.3 + DeepSeek + 中国天气网 API。前端零框架。

**File Map (3 个文件，2 个新增 1 个修改):**

| 文件 | 操作 | 职责 |
|---|---|---|
| `travel-agent/src/app.py` | 新增 | FastAPI 后端 — 端点 + Agent 消息解析 |
| `travel-agent/src/static/index.html` | 新增 | 前端单页面 — 聊天界面 + 推理链可视化 |
| `travel-agent/requirements.txt` | 修改 | 增加 `fastapi` + `uvicorn` |

---

### Task 1: FastAPI 后端（app.py）

**产出:** `src/app.py` — POST /api/chat 端点 + Agent 消息解析逻辑

**Files:**
- Create: `travel-agent/src/app.py`

- [ ] **Step 1: 创建 static 目录**

```bash
mkdir -p travel-agent/src/static
```

- [ ] **Step 2: 写 app.py**

`travel-agent/src/app.py`:
```python
"""
旅行助手 Agent — Web API 后端

FastAPI 应用，提供 POST /api/chat 端点。
前端调用此端点，后端运行 Agent，解析消息链，返回推理步骤 + 最终答案。

运行方式：
    cd travel-agent
    uvicorn src.app:app --reload --port 8000

然后浏览器打开 http://localhost:8000
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from src.agent import create_travel_agent
from langchain_core.messages import AIMessage, ToolMessage

# 加载 .env 环境变量（必须在使用 API Key 之前）
load_dotenv()

# 创建 FastAPI 应用实例
app = FastAPI(title="智能旅行助手 Agent")


# ── 请求/响应模型 ──────────────────────────────────

class ChatRequest(BaseModel):
    """前端发送的聊天请求"""
    query: str


# ── Agent 消息解析逻辑 ─────────────────────────────

def extract_steps_and_answer(messages: list) -> tuple[list[dict], str]:
    """从 LangChain Agent 返回的消息列表中提取推理步骤和最终答案。

    Agent 返回的 messages 包含：
    - HumanMessage: 用户输入
    - AIMessage (含 tool_calls): Agent 决定调用工具
    - ToolMessage: 工具执行结果
    - AIMessage (不含 tool_calls): 最终回答

    Args:
        messages: Agent.invoke() 返回的 messages 列表

    Returns:
        (steps, answer): steps 是推理步骤列表，answer 是最终回答字符串
    """
    steps = []
    tool_names = {
        "get_weather": "查询天气",
        "recommend_spot": "推荐景点",
    }

    for msg in messages:
        # AIMessage 包含 tool_calls → Agent 决定调用工具
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                steps.append({
                    "round": len(steps) + 1,
                    "thought": msg.content or f"需要调用 {tc['name']} 工具",
                    "tool": tc["name"],
                    "tool_label": tool_names.get(tc["name"], tc["name"]),
                    "tool_input": str(tc.get("args", {})),
                    "observation": None,  # 下一步由 ToolMessage 填充
                    "tool_call_id": tc["id"],
                })

        # ToolMessage → 工具执行结果，填入上一步的 observation
        elif isinstance(msg, ToolMessage):
            tool_call_id = getattr(msg, "tool_call_id", None)
            if tool_call_id:
                for step in reversed(steps):
                    if step.get("tool_call_id") == tool_call_id and step["observation"] is None:
                        step["observation"] = str(msg.content)
                        break

    # 找最后一个不含 tool_calls 的 AIMessage → 最终答案
    answer = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls and msg.content:
            answer = msg.content
            break

    # 清理内部字段 tool_call_id（前端不需要）
    for step in steps:
        step.pop("tool_call_id", None)

    return steps, answer


# ── API 端点 ───────────────────────────────────────

@app.post("/api/chat")
def chat(request: ChatRequest):
    """处理聊天请求，运行 Agent 并返回结果。

    1. 创建 Agent 实例
    2. 用用户输入运行 Agent
    3. 解析消息链 → 推理步骤 + 最终答案
    4. 返回 JSON
    """
    agent = create_travel_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": request.query}]})
    steps, answer = extract_steps_and_answer(result["messages"])
    return {
        "steps": steps,
        "answer": answer,
    }


# ── 静态文件挂载 ───────────────────────────────────
# FastAPI 先检查注册的路由（/api/chat），未命中再走静态文件
# html=True: 访问 / 自动返回 index.html
app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
```

**代码含义说明：**
- `ChatRequest(BaseModel)` — FastAPI 自动校验请求体必须包含 `query` 字段
- `extract_steps_and_answer()` — 核心解析函数。遍历 messages，AIMessage(含tool_calls) 记录为步骤、ToolMessage 填充 observation、最后的 AIMessage 作为最终回答
- `tool_label` — 中文标签映射，前端用来显示"查询天气"比"get_weather"更友好
- `app.mount("/", ..., html=True)` — 必须放在路由定义之后，FastAPI 会先匹配路由再 fallback 到静态文件

- [ ] **Step 3: 验证 FastAPI 导入和路由**

```bash
cd travel-agent
python -c "
from dotenv import load_dotenv
load_dotenv()
from src.app import app
print('FastAPI app:', app.title)
print('Routes:', [r.path for r in app.routes])
# 确认 /api/chat 和 / 都被注册
paths = [r.path for r in app.routes]
assert '/api/chat' in str(paths), 'POST /api/chat not found'
print('Route check OK')
"
```

Expected: 输出包含 `FastAPI app: 智能旅行助手 Agent`，路由包含 `/api/chat`

- [ ] **Step 4: Commit**

```bash
git add travel-agent/src/app.py travel-agent/src/static/
git commit -m "feat: add FastAPI backend with agent message parsing"
```

---

### Task 2: 前端页面（index.html）

**产出:** `src/static/index.html` — 完整的聊天界面 + 推理链可视化

**Files:**
- Create: `travel-agent/src/static/index.html`

- [ ] **Step 1: 写 index.html**

`travel-agent/src/static/index.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能旅行助手</title>
    <style>
        /* ── 全局重置 ──────────────────────────── */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #E8F5E9 0%, #E3F2FD 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* ── 顶栏 ──────────────────────────────── */
        header {
            background: linear-gradient(90deg, #43A047, #1E88E5);
            color: white;
            padding: 16px 24px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        header h1 {
            font-size: 20px;
            font-weight: 600;
        }
        header .logo {
            font-size: 28px;
        }

        /* ── 聊天区域 ──────────────────────────── */
        #chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            max-width: 800px;
            width: 100%;
            margin: 0 auto;
        }

        .message {
            margin-bottom: 20px;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* ── 用户消息气泡 ──────────────────────── */
        .user-message {
            display: flex;
            justify-content: flex-end;
        }
        .user-message .bubble {
            background: #E8F5E9;
            border: 1px solid #A5D6A7;
            border-radius: 16px 16px 4px 16px;
            padding: 12px 18px;
            max-width: 75%;
            font-size: 15px;
            color: #2E7D32;
        }
        .user-message .bubble .sender {
            display: block;
            font-size: 11px;
            color: #66BB6A;
            margin-bottom: 4px;
            font-weight: 600;
        }

        /* ── 推理链卡片 ────────────────────────── */
        .reasoning-chain {
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        .reasoning-chain .chain-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            background: #F1F8E9;
            cursor: pointer;
            user-select: none;
            font-size: 14px;
            font-weight: 600;
            color: #33691E;
        }
        .reasoning-chain .chain-header .arrow {
            transition: transform 0.2s;
            font-size: 12px;
        }
        .reasoning-chain .chain-body {
            padding: 0 16px;
            max-height: 800px;
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease;
        }
        .reasoning-chain.collapsed .chain-body {
            max-height: 0;
            padding-top: 0;
            padding-bottom: 0;
        }
        .reasoning-chain.collapsed .arrow {
            transform: rotate(-90deg);
        }

        .chain-step {
            border-left: 3px solid #43A047;
            padding: 10px 14px;
            margin: 12px 0;
            background: #F9FBE7;
            border-radius: 0 8px 8px 0;
            font-size: 13px;
            line-height: 1.6;
        }
        .chain-step .step-label {
            font-weight: 600;
            font-size: 12px;
            color: #558B2F;
        }
        .chain-step .step-detail {
            color: #555;
            margin: 2px 0;
        }
        .chain-step .step-tool {
            color: #1565C0;
            font-family: monospace;
            font-size: 12px;
        }
        .chain-step .step-obs {
            color: #333;
            background: #FFF8E1;
            padding: 6px 10px;
            border-radius: 6px;
            margin-top: 4px;
            font-size: 13px;
        }

        /* ── Agent 回答气泡 ────────────────────── */
        .agent-answer {
            display: flex;
            justify-content: flex-start;
        }
        .agent-answer .bubble {
            background: #E3F2FD;
            border: 1px solid #90CAF9;
            border-radius: 16px 16px 16px 4px;
            padding: 14px 18px;
            max-width: 85%;
            font-size: 14px;
            color: #0D47A1;
            line-height: 1.7;
            white-space: pre-wrap;
        }
        .agent-answer .bubble .sender {
            display: block;
            font-size: 11px;
            color: #42A5F5;
            margin-bottom: 6px;
            font-weight: 600;
        }

        /* ── Loading ───────────────────────────── */
        .loading {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            color: #888;
            font-size: 14px;
        }
        .loading .dots span {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #43A047;
            animation: bounce 1.2s infinite;
        }
        .loading .dots span:nth-child(2) { animation-delay: 0.2s; }
        .loading .dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-6px); }
        }

        /* ── 输入区域 ──────────────────────────── */
        footer {
            background: white;
            border-top: 1px solid #E0E0E0;
            padding: 12px 20px;
        }
        .input-row {
            display: flex;
            gap: 10px;
            max-width: 800px;
            margin: 0 auto;
        }
        .input-row input {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #E0E0E0;
            border-radius: 24px;
            font-size: 15px;
            outline: none;
            transition: border-color 0.2s;
        }
        .input-row input:focus {
            border-color: #43A047;
        }
        .input-row button {
            background: #43A047;
            color: white;
            border: none;
            border-radius: 24px;
            padding: 12px 24px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .input-row button:hover {
            background: #388E3C;
        }
        .input-row button:disabled {
            background: #C8E6C9;
            cursor: not-allowed;
        }
    </style>
</head>
<body>

    <!-- 顶栏 -->
    <header>
        <span class="logo">&#x1F333;</span>
        <h1>智能旅行助手</h1>
    </header>

    <!-- 聊天区域 -->
    <div id="chat-area">
        <div style="text-align:center; color:#999; padding:40px 0; font-size:14px;">
            &#x1F30D; 告诉我你想去哪里，我帮你查天气、推荐景点
        </div>
    </div>

    <!-- 加载指示器（默认隐藏） -->
    <div id="loading" class="loading" style="display:none; padding:12px 20px; max-width:800px; margin:0 auto;">
        思考中<span class="dots"><span></span><span></span><span></span></span>
    </div>

    <!-- 输入区域 -->
    <footer>
        <div class="input-row">
            <input
                id="query-input"
                type="text"
                placeholder="请输入您的问题，例如：今天北京天气怎么样？"
                autocomplete="off"
            />
            <button id="send-btn" onclick="sendMessage()">&#x2708;&#xFE0F; 发送</button>
        </div>
    </footer>

    <script>
        const chatArea = document.getElementById('chat-area');
        const queryInput = document.getElementById('query-input');
        const sendBtn = document.getElementById('send-btn');
        const loadingEl = document.getElementById('loading');

        // 回车发送
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        /**
         * 发送消息到后端，渲染结果
         */
        async function sendMessage() {
            const query = queryInput.value.trim();
            if (!query) return;

            // 清除初始提示（如果有的话）
            const placeholder = chatArea.querySelector('div:first-child');
            if (placeholder && placeholder.style.textAlign === 'center' && chatArea.children.length === 1) {
                chatArea.innerHTML = '';
            }

            // 显示用户消息
            addUserMessage(query);
            queryInput.value = '';
            setLoading(true);

            try {
                const resp = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query }),
                });

                if (!resp.ok) {
                    throw new Error(`服务器错误: ${resp.status}`);
                }

                const data = await resp.json();

                // 渲染推理链
                if (data.steps && data.steps.length > 0) {
                    addReasoningChain(data.steps);
                }

                // 渲染最终回答
                if (data.answer) {
                    addAgentAnswer(data.answer);
                }

            } catch (err) {
                addError(err.message);
            } finally {
                setLoading(false);
                scrollToBottom();
            }
        }

        function addUserMessage(text) {
            const div = document.createElement('div');
            div.className = 'message user-message';
            div.innerHTML = `
                <div class="bubble">
                    <span class="sender">You</span>
                    ${escapeHtml(text)}
                </div>`;
            chatArea.appendChild(div);
            scrollToBottom();
        }

        function addReasoningChain(steps) {
            const div = document.createElement('div');
            div.className = 'message';

            let stepsHtml = '';
            for (const step of steps) {
                stepsHtml += `
                    <div class="chain-step">
                        <div class="step-label">&#x1F52E; Round ${step.round} — ${escapeHtml(step.tool_label || step.tool)}</div>
                        <div class="step-detail">&#x1F4AD; 思考：${escapeHtml(step.thought)}</div>
                        <div class="step-tool">&#x1F527; 调用：${escapeHtml(step.tool)}(${escapeHtml(step.tool_input)})</div>
                        <div class="step-obs">&#x1F4CA; 结果：${escapeHtml(step.observation || '等待中...')}</div>
                    </div>`;
            }

            div.innerHTML = `
                <div class="reasoning-chain">
                    <div class="chain-header" onclick="toggleChain(this)">
                        <span class="arrow">&#x25BC;</span>
                        &#x1F9E0; Agent 推理过程（${steps.length} 轮）
                    </div>
                    <div class="chain-body">${stepsHtml}</div>
                </div>`;

            chatArea.appendChild(div);
            scrollToBottom();
        }

        function addAgentAnswer(text) {
            const div = document.createElement('div');
            div.className = 'message agent-answer';
            div.innerHTML = `
                <div class="bubble">
                    <span class="sender">&#x1F30D; 旅行助手</span>
                    ${escapeHtml(text).replace(/\n/g, '<br>')}
                </div>`;
            chatArea.appendChild(div);
            scrollToBottom();
        }

        function addError(msg) {
            const div = document.createElement('div');
            div.className = 'message agent-answer';
            div.innerHTML = `
                <div class="bubble" style="background:#FFEBEE;border-color:#EF9A9A;color:#C62828;">
                    <span class="sender" style="color:#EF5350;">Error</span>
                    ${escapeHtml(msg)}
                </div>`;
            chatArea.appendChild(div);
            scrollToBottom();
        }

        function setLoading(loading) {
            loadingEl.style.display = loading ? 'flex' : 'none';
            sendBtn.disabled = loading;
            queryInput.disabled = loading;
        }

        function toggleChain(header) {
            header.parentElement.classList.toggle('collapsed');
        }

        function scrollToBottom() {
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function escapeHtml(text) {
            const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
            return String(text).replace(/[&<>"']/g, c => map[c]);
        }
    </script>

</body>
</html>
```

**代码含义说明：**
- CSS 全在 `<style>` 里，零外部依赖。配色严格遵循自然清新风：`#43A047` 绿 + `#1E88E5` 蓝渐变顶栏
- 用户消息右对齐（`flex-end`），绿色底；Agent 回答左对齐，淡蓝底
- 推理链卡片默认展开，点击 `chain-header` 切换 `.collapsed` 类折叠
- `escapeHtml()` 防 XSS。`fetch()` 调后端 API
- Loading 状态用三个弹跳圆点，禁输入。动画 `bounce` 纯 CSS
- 三个核心渲染函数：`addUserMessage`、`addReasoningChain`、`addAgentAnswer`，职责分明

- [ ] **Step 2: 验证 HTML 文件存在且结构完整**

```bash
# 验证文件非空，包含关键元素
grep -c "智能旅行助手" travel-agent/src/static/index.html
grep -c "api/chat" travel-agent/src/static/index.html
grep -c "reasoning-chain" travel-agent/src/static/index.html
```

Expected: 三个 grep 都返回至少 1 次匹配。

- [ ] **Step 3: Commit**

```bash
git add travel-agent/src/static/index.html
git commit -m "feat: add web frontend with reasoning chain visualization"
```

---

### Task 3: 更新依赖 + 端到端验证

**产出:** 更新 `requirements.txt`，安装新依赖，启动服务，验证端到端流程

**Files:**
- Modify: `travel-agent/requirements.txt`

- [ ] **Step 1: 更新 requirements.txt**

`travel-agent/requirements.txt`:
```txt
langchain>=0.3.0
langchain-openai>=0.2.0
requests>=2.32.0
python-dotenv>=1.0.0
fastapi>=0.115.0
uvicorn>=0.34.0
```

- [ ] **Step 2: 安装新依赖**

```bash
cd travel-agent
pip install fastapi uvicorn
```

Expected: 两个包安装成功，无报错。

- [ ] **Step 3: 启动 FastAPI 服务**

```bash
cd travel-agent
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000
```

Expected: 输出 `Uvicorn running on http://0.0.0.0:8000`

手动打开浏览器 http://localhost:8000，应看到智能旅行助手界面。输入问题并验证。

- [ ] **Step 4: 端到端 API 测试（终端）**

打开新终端：
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"查询今天北京天气，推荐景点"}'
```

Expected: 返回 JSON，包含 `steps`（至少 2 轮）和 `answer`（非空）。

逐项验收：

| 检查项 | 标准 |
|---|---|
| ✅ 浏览器界面 | 打开 localhost:8000 看到绿色渐变顶栏 + 输入区 |
| ✅ API 返回 steps | 至少 2 轮推理步骤 |
| ✅ API 返回 answer | 非空回答字符串 |
| ✅ 推理步骤顺序 | get_weather 在前，recommend_spot 在后 |
| ✅ 工具调用数据 | steps 中每个 step 有 tool, tool_input, observation |
| ✅ 前端渲染 | 用户气泡 + 推理链卡片 + Agent 回答 |
| ✅ 推理链可折叠 | 点击卡片头折叠/展开 |
| ✅ 配色 | 薄荷绿渐变顶栏 + 绿色/蓝色气泡 |

- [ ] **Step 5: Commit**

```bash
git add travel-agent/requirements.txt
git commit -m "chore: add fastapi and uvicorn dependencies"
```
