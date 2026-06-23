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

# 加载 .env 文件中的环境变量（必须在导入 agent 之前调用）
load_dotenv()

from src.agent import create_travel_agent


def check_env() -> bool:
    """检查必要的环境变量是否已配置"""
    missing = []
    if not os.getenv("DEEPSEEK_API_KEY"):
        missing.append("DEEPSEEK_API_KEY")

    if missing:
        print("=" * 60)
        print("[X] 缺少以下环境变量配置：")
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
    print("***智能旅行助手 Agent")
    print("=" * 60)
    print("提示：输入 'exit' 或 'quit' 退出")
    print()

    if not check_env():
        sys.exit(1)

    print("[OK] 环境配置检查通过，正在初始化 Agent...")
    agent = create_travel_agent()
    print("[OK] Agent 就绪！")
    print()

    # ── 交互循环 ──────────────────────────────────
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye! 再见！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("Bye! 再见！")
            break

        print("\n" + "─" * 60)
        print("[Agent] Agent 思考中...\n")

        try:
            # LangChain 1.3: create_agent 返回 CompiledStateGraph
            # 输入格式: {"messages": [{"role": "user", "content": "..."}]}
            # 输出格式: {"messages": [..., AIMessage(content="最终回答")]}
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]}
            )

            # 提取最后一条消息（Agent 的最终回答）
            final_message = result["messages"][-1]
            print("\n" + "─" * 60)
            print("[Answer] 最终回答：")
            print(final_message.content)
            print("─" * 60 + "\n")

        except Exception as e:
            print(f"\n[X] Agent 运行出错：{e}\n")


if __name__ == "__main__":
    main()
