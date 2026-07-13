"""
Custom LangChain-compatible chat model that talks directly to the deployed vLLM
service. Unlike ``langchain_openai.ChatOpenAI``, this model preserves the
non-standard ``reasoning`` field returned by the Qwen3.6-27B-FP8 deployment,
so the agent can stream the model's thinking process to the frontend.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolCallChunk,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.tools import StructuredTool


def _convert_message_to_openai_dict(message: BaseMessage) -> dict[str, Any]:
    """Convert a LangChain message to the OpenAI / vLLM chat format."""
    if isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    if isinstance(message, HumanMessage):
        return {"role": "user", "content": message.content}
    if isinstance(message, AIMessage):
        item: dict[str, Any] = {"role": "assistant", "content": message.content or ""}
        if getattr(message, "tool_calls", None):
            item["tool_calls"] = [
                {
                    "id": tc.get("id"),
                    "type": "function",
                    "function": {
                        "name": tc.get("name"),
                        "arguments": json.dumps(tc.get("args", {}), ensure_ascii=False),
                    },
                }
                for tc in message.tool_calls
            ]
        return item
    if isinstance(message, ToolMessage):
        return {
            "role": "tool",
            "tool_call_id": message.tool_call_id,
            "content": message.content,
        }
    return {"role": "user", "content": str(message.content)}


class MyVLLMChatModel(BaseChatModel):
    """vLLM-backed chat model that exposes the ``reasoning`` field.

    The deployed Qwen3.6-27B-FP8 service returns a structured ``reasoning``
    field alongside ``content``. Standard LangChain ChatOpenAI drops this field,
    so this custom model calls the vLLM HTTP API directly and surfaces it in
    ``AIMessage.additional_kwargs["reasoning"]``.
    """

    model: str = ""
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.2
    timeout: float = 120.0
    tools: list[dict[str, Any]] | None = None

    def _get_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=httpx.Timeout(self.timeout, connect=10.0),
            trust_env=False,
        )

    def _build_payload(
        self,
        messages: list[BaseMessage],
        stream: bool,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_convert_message_to_openai_dict(m) for m in messages],
            "stream": stream,
            "temperature": self.temperature,
        }
        if self.tools:
            payload["tools"] = self.tools
            payload["tool_choice"] = "auto"
        payload.update(kwargs)
        return payload

    @staticmethod
    def _parse_tool_calls(raw_tool_calls: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if not raw_tool_calls:
            return []
        parsed: list[dict[str, Any]] = []
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            args: dict[str, Any]
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {"raw": func.get("arguments", "")}
            parsed.append({
                "id": tc.get("id"),
                "name": func.get("name"),
                "args": args,
            })
        return parsed

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        with self._get_client() as client:
            response = client.post(
                "/chat/completions",
                json=self._build_payload(messages, stream=False, **kwargs),
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        msg = choice["message"]
        additional_kwargs: dict[str, Any] = {}
        if msg.get("reasoning"):
            additional_kwargs["reasoning"] = msg["reasoning"]

        message = AIMessage(
            content=msg.get("content") or "",
            additional_kwargs=additional_kwargs,
            tool_calls=self._parse_tool_calls(msg.get("tool_calls")),
        )
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream tokens from vLLM while capturing reasoning fragments."""
        with self._get_client() as client:
            with client.stream(
                "POST",
                "/chat/completions",
                json=self._build_payload(messages, stream=True, **kwargs),
            ) as response:
                if not response.is_success:
                    raise httpx.HTTPStatusError(
                        f"vLLM returned {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                for line in response.iter_lines():
                    if not line or line.startswith(":"):
                        continue
                    if line == "data: [DONE]":
                        break
                    if not line.startswith("data: "):
                        continue

                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    choice = data.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    content = delta.get("content") or ""
                    reasoning = delta.get("reasoning")
                    raw_tool_calls = delta.get("tool_calls")

                    additional_kwargs: dict[str, Any] = {}
                    if reasoning:
                        additional_kwargs["reasoning"] = reasoning

                    tool_call_chunks: list[ToolCallChunk] = []
                    if raw_tool_calls:
                        for tc in raw_tool_calls:
                            func = tc.get("function", {}) or {}
                            tool_call_chunks.append(
                                ToolCallChunk(
                                    name=func.get("name"),
                                    args=func.get("arguments"),
                                    id=tc.get("id"),
                                    index=tc.get("index", 0),
                                    type="tool_call_chunk",
                                )
                            )

                    yield ChatGenerationChunk(
                        message=AIMessageChunk(
                            content=content,
                            additional_kwargs=additional_kwargs,
                            tool_call_chunks=tool_call_chunks,
                        )
                    )

    def bind_tools(self, tools: list[Any], **kwargs: Any) -> "MyVLLMChatModel":
        """Bind tools in OpenAI-compatible format."""
        openai_tools: list[dict[str, Any]] = []
        for tool in tools:
            if isinstance(tool, StructuredTool):
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.args_schema.model_json_schema(),
                    },
                })
            elif isinstance(tool, dict):
                openai_tools.append(tool)

        return self.model_copy(update={"tools": openai_tools})

    @property
    def _llm_type(self) -> str:
        return "my-vllm-chat"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model": self.model, "base_url": self.base_url}
