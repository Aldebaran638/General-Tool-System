"""
演示：文档解析 + 本地大模型提取填空题。

本脚本不会保存任何数据到数据库，仅用于演示：
  1. 将 .docx（或 .pdf）试卷解析为原始文本
  2. 使用 LangGraph 编排流程，httpx 直接调用本地 OpenAI 兼容模型
  3. 将填空题提取为结构化 JSON

用法：
  pip install -r test/requirements.txt
  python test/extract_fill_blank_demo.py test/题目1.docx

环境变量：
  LLM_BASE_URL=http://192.168.3.242:1995/v1
  LLM_MODEL=Qwen3.6-27B-FP8
  LLM_API_KEY=sk-anything   # 本地模型通常忽略该字段
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, TypedDict

import httpx

from docx import Document

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore[assignment]

from langgraph.graph import END, START, StateGraph


# ─── 配置 ─────────────────────────────────────────────────────────────────────

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://192.168.3.242:1995/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen3.6-27B-FP8")
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-anything")


class Extraction2State(TypedDict):
    userPrompt: str
    result: str
    error: str | None
    retry_count: int

class LLMResponse(TypedDict):
    response: str

def call_llm(system: str, user: str) -> dict[str, Any]:
    """使用 httpx 直接调用本地 OpenAI 兼容模型，返回解析后的 JSON。"""
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    with httpx.Client(timeout=120, trust_env=False) as client:
        response = client.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    # 持久化原始响应，方便调试。
    Path("llm_raw_response.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    msg = data["choices"][0]["message"]
    content = msg.get("content") or msg.get("reasoning") or ""
    Path("llm_content.txt").write_text(content, encoding="utf-8")

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM 返回的内容不是合法 JSON: {e}\n"
            f"正在重试"
        ) from e

def llm_node(state: Extraction2State) -> Extraction2State:
    system = "你好!请回复中文。你必须只返回合法 JSON，不要输出任何其他内容。"
    user = state["userPrompt"]

    if state.get("error") and state.get("retry_count", 0) > 0:
        user = (
            f"{user}\n\n"
            f"上一次返回失败，错误信息：{state['error']}\n"
            f"请修正问题，严格返回合法 JSON 格式，不要包含 markdown 代码块或解释文字。"
        )

    try:
        result = call_llm(system, user)
        return {
            **state,
            "result": json.dumps(result, ensure_ascii=False),
            "error": None,
        }
    except ValueError as e:
        # 记录重试日志
        log_line = f"[retry {state.get('retry_count', 0)}] error: {e}\n"
        Path("llm_retry.log").write_text(
            Path("llm_retry.log").read_text(encoding="utf-8") + log_line
            if Path("llm_retry.log").exists()
            else log_line,
            encoding="utf-8",
        )
        return {
            **state,
            "error": str(e),
            "retry_count": state.get("retry_count", 0) + 1,
        }

def should_retry(state: Extraction2State) -> str:
    """判断是否需要重试：出错且重试次数小于 3 次时继续重试。"""
    if state.get("error") and state.get("retry_count", 0) < 3:
        return "retry"
    return "end"


def build_graph() -> StateGraph:
    builder = StateGraph(Extraction2State)

    builder.add_node("LLM", llm_node)
    builder.add_edge(START, "LLM")
    builder.add_conditional_edges(
        "LLM",
        should_retry,
        {"retry": "LLM", "end": END},
    )

    return builder.compile()


# ─── 主函数 ───────────────────────────────────────────────────────────────────

def main() -> int:
    graph = build_graph()
    final_state = graph.invoke({
        "userPrompt": "你好,我是三体人.不要回复",
        "result": "",
        "error": None,
        "retry_count": 0,
    })
    print(final_state.get("result"))
    if final_state.get("error"):
        print(f"最终失败: {final_state['error']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
