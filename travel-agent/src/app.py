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
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from src.agent import create_travel_agent
from langchain_core.messages import AIMessage, ToolMessage

# 加载 .env 环境变量（必须在使用 API Key 之前）
load_dotenv()

# 创建 FastAPI 应用实例
app = FastAPI(title="智能旅行助手 Agent")

# 在模块级别创建 Agent，复用避免每次请求都重新编译
travel_agent = create_travel_agent()


# ── 请求/响应模型 ──────────────────────────────────

class ChatRequest(BaseModel):
    """前端发送的聊天请求"""
    query: str


# ── Agent 消息解析逻辑 ─────────────────────────────

def extract_steps_and_answer(messages: list) -> tuple[list[dict], str]:
    """从 LangChain Agent 返回的消息列表中提取推理步骤和最终答案。"""
    steps = []
    tool_names = {
        "get_weather": "查询天气",
        "recommend_spot": "推荐景点",
    }

    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                steps.append({
                    "round": len(steps) + 1,
                    "thought": msg.content or f"需要调用 {tc['name']} 工具",
                    "tool": tc["name"],
                    "tool_label": tool_names.get(tc["name"], tc["name"]),
                    "tool_input": str(tc.get("args", {})),
                    "observation": None,
                    "tool_call_id": tc["id"],
                })

        elif isinstance(msg, ToolMessage):
            tool_call_id = getattr(msg, "tool_call_id", None)
            if tool_call_id:
                for step in reversed(steps):
                    if step.get("tool_call_id") == tool_call_id and step["observation"] is None:
                        step["observation"] = str(msg.content)
                        break

    answer = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls and msg.content:
            answer = msg.content
            break

    for step in steps:
        step.pop("tool_call_id", None)

    return steps, answer


# ── API 端点 ───────────────────────────────────────

@app.post("/api/chat")
def chat(request: ChatRequest):
    """处理聊天请求，运行 Agent 并返回结果。"""
    try:
        result = travel_agent.invoke({"messages": [{"role": "user", "content": request.query}]})
        steps, answer = extract_steps_and_answer(result["messages"])
        return {
            "steps": steps,
            "answer": answer,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Agent invocation failed", "detail": str(e)},
        )


# ── 静态文件挂载 ───────────────────────────────────
app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
