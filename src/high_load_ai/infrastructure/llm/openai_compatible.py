from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from high_load_ai.core.config import Settings


class OpenAICompatibleClient:
    """OpenAI-compatible chat model client with streaming token chunks."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = ChatOpenAI(
            base_url=settings.llm_base_url,
            api_key=SecretStr(settings.llm_api_key),
            model=settings.llm_model,
            temperature=0.2,
            timeout=settings.llm_timeout_seconds,
            streaming=True,
        )

    async def astream(
        self,
        prompt: str,
        run_id: str,
        *,
        callbacks: list[Any] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        yield {"event": "progress", "data": f"run={run_id}:llm_started"}

        config: RunnableConfig = {}
        if callbacks:
            config["callbacks"] = callbacks
            config["metadata"] = {"langfuse_session_id": run_id}

        async def _stream() -> AsyncIterator[AIMessageChunk]:
            async for chunk in self._model.astream([HumanMessage(content=prompt)], config=config):
                yield chunk

        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(Exception),
                wait=wait_exponential_jitter(initial=1, max=20),
                stop=stop_after_attempt(4),
                reraise=True,
            ):
                with attempt:
                    async for chunk in _stream():
                        token = _chunk_text(chunk)
                        if token:
                            yield {"event": "token", "token": token}
                    break
        finally:
            yield {"event": "progress", "data": f"run={run_id}:llm_completed"}


def _chunk_text(chunk: AIMessageChunk) -> str:
    content = chunk.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return ""
