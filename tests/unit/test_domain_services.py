from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

import pytest

from high_load_ai.domain.models import AgentRun
from high_load_ai.domain.ports import AgentExecutor, AgentRunRepository, Tracer
from high_load_ai.domain.services import StartAgentRunService, StreamAgentRunService


class InMemoryRepo(AgentRunRepository):
    def __init__(self) -> None:
        self.store: dict[UUID, AgentRun] = {}

    async def create(self, run: AgentRun) -> AgentRun:
        self.store[run.id.value] = run
        return run

    async def update(self, run: AgentRun) -> AgentRun:
        self.store[run.id.value] = run
        return run

    async def get(self, run_id: UUID) -> AgentRun | None:
        return self.store.get(run_id)


class FakeExecutor(AgentExecutor):
    async def astream(
        self,
        prompt: str,
        run_id: str,
        *,
        callbacks: list[object] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        _ = prompt
        _ = run_id
        _ = callbacks
        yield {"event": "token", "token": "hello "}
        yield {"event": "token", "token": "world"}


class FakeTracer(Tracer):
    def start_span(self, name: str, metadata: dict[str, str] | None = None) -> object:
        return {"name": name, "metadata": metadata or {}}

    def end_span(self, span: object, *, status: str) -> None:
        _ = span
        _ = status


@pytest.mark.asyncio
async def test_start_and_stream_run_service() -> None:
    repo = InMemoryRepo()
    start_service = StartAgentRunService(repo)
    run = await start_service.execute("say hi")

    stream_service = StreamAgentRunService(repo, FakeExecutor(), FakeTracer())
    events = [event async for event in stream_service.execute(run)]

    assert events[-1]["event"] == "done"
    assert run.output_text == "hello world"
    assert run.status.value == "completed"
