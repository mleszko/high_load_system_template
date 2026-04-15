from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)


class OpenAIModelClient:
    """Single OpenAI-compatible chat model: streaming tokens and full-text invoke."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        temperature: float = 0.2,
    ) -> None:
        self._model = ChatOpenAI(
            base_url=base_url,
            api_key=SecretStr(api_key),
            model=model,
            temperature=temperature,
            timeout=timeout_seconds,
            streaming=True,
        )

    async def astream(
        self,
        prompt: str,
        *,
        callbacks: list[Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        config: RunnableConfig = {}
        if callbacks:
            config["callbacks"] = callbacks
        if metadata:
            config["metadata"] = metadata

        async def _chunks() -> AsyncIterator[AIMessageChunk]:
            async for chunk in self._model.astream([HumanMessage(content=prompt)], config=config):
                yield chunk

        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(Exception),
            wait=wait_exponential_jitter(initial=1, max=20),
            stop=stop_after_attempt(4),
            reraise=True,
        ):
            with attempt:
                async for chunk in _chunks():
                    token = _chunk_text(chunk)
                    if token:
                        yield {"event": "token", "token": token}
                break

    async def ainvoke_text(
        self,
        prompt: str,
        *,
        callbacks: list[Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        config: RunnableConfig = {}
        if callbacks:
            config["callbacks"] = callbacks
        if metadata:
            config["metadata"] = metadata

        result: str | None = None
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(Exception),
            wait=wait_exponential_jitter(initial=1, max=20),
            stop=stop_after_attempt(4),
            reraise=True,
        ):
            with attempt:
                message: AIMessage = await self._model.ainvoke(
                    [HumanMessage(content=prompt)],
                    config=config,
                )
                result = str(message.content)
                break

        if result is None:
            raise RuntimeError("LLM invoke produced no result")
        return result


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
