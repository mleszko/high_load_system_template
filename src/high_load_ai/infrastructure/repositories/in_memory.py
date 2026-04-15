from __future__ import annotations

from uuid import UUID

from high_load_ai.domain.models import AgentRun
from high_load_ai.domain.ports import AgentRunRepository


class InMemoryAgentRunRepository(AgentRunRepository):
    def __init__(self) -> None:
        self._runs: dict[UUID, AgentRun] = {}

    async def create(self, run: AgentRun) -> AgentRun:
        self._runs[run.id.value] = run
        return run

    async def get(self, run_id: UUID) -> AgentRun | None:
        return self._runs.get(run_id)

    async def update(self, run: AgentRun) -> AgentRun:
        self._runs[run.id.value] = run
        return run
