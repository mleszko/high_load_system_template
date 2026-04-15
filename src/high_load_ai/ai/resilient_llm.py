from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from high_load_ai.ai.circuit_breaker import CircuitBreakerState
from high_load_ai.infrastructure.llm.openai_model import OpenAIModelClient

logger = logging.getLogger(__name__)


class ResilientLlmExecutor:
    """Primary model with circuit breaker; falls back to secondary model on failure or open circuit."""

    def __init__(
        self,
        primary: OpenAIModelClient,
        fallback: OpenAIModelClient,
        breaker: CircuitBreakerState,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._breaker = breaker

    def _meta(self, run_id: str) -> dict[str, Any]:
        from high_load_ai.core.context import get_correlation_id

        meta: dict[str, Any] = {"langfuse_session_id": run_id}
        cid = get_correlation_id()
        if cid:
            meta["correlation_id"] = cid
        return meta

    async def astream(
        self,
        prompt: str,
        run_id: str,
        *,
        callbacks: list[Any] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        metadata = self._meta(run_id)
        use_fallback = self._breaker.is_open

        if use_fallback:
            logger.warning("circuit_breaker_open_using_fallback_stream run_id=%s", run_id)
            async for ev in self._fallback.astream(prompt, callbacks=callbacks, metadata=metadata):
                yield ev
            self._breaker.record_success()
            return

        try:
            async for ev in self._primary.astream(prompt, callbacks=callbacks, metadata=metadata):
                yield ev
            self._breaker.record_success()
        except Exception:
            self._breaker.record_failure()
            logger.exception("primary_llm_stream_failed_fallback run_id=%s", run_id)
            async for ev in self._fallback.astream(prompt, callbacks=callbacks, metadata=metadata):
                yield ev
            self._breaker.record_success()

    async def ainvoke_text(
        self,
        prompt: str,
        run_id: str,
        *,
        callbacks: list[Any] | None = None,
    ) -> str:
        metadata = self._meta(run_id)
        use_fallback = self._breaker.is_open

        if use_fallback:
            logger.warning("circuit_breaker_open_using_fallback_invoke run_id=%s", run_id)
            text = await self._fallback.ainvoke_text(prompt, callbacks=callbacks, metadata=metadata)
            self._breaker.record_success()
            return text

        try:
            text = await self._primary.ainvoke_text(prompt, callbacks=callbacks, metadata=metadata)
            self._breaker.record_success()
            return text
        except Exception:
            self._breaker.record_failure()
            logger.exception("primary_llm_invoke_failed_fallback run_id=%s", run_id)
            text = await self._fallback.ainvoke_text(prompt, callbacks=callbacks, metadata=metadata)
            self._breaker.record_success()
            return text
