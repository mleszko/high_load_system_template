from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol
from uuid import UUID

from high_load_ai.domain.models import AgentRun


class AgentRunRepository(Protocol):
    async def create(self, run: AgentRun) -> AgentRun: ...

    async def update(self, run: AgentRun) -> AgentRun: ...

    async def get(self, run_id: UUID) -> AgentRun | None: ...


class AgentExecutor(Protocol):
    def astream(
        self,
        prompt: str,
        run_id: str,
        *,
        callbacks: list[Any] | None = None,
    ) -> AsyncIterator[dict[str, str]]: ...


class RateLimiter(Protocol):
    async def allow(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]: ...


class Tracer(Protocol):
    def start_span(self, name: str, metadata: dict[str, str] | None = None) -> object: ...

    def end_span(self, span: object, *, status: str) -> None: ...
