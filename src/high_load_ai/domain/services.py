from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from high_load_ai.domain.models import AgentRun, RunId
from high_load_ai.domain.ports import AgentExecutor, AgentRunRepository, Tracer


class StartAgentRunService:
    def __init__(self, repository: AgentRunRepository) -> None:
        self._repository = repository

    async def execute(self, prompt: str) -> AgentRun:
        run = AgentRun(id=RunId.new(), prompt=prompt)
        return await self._repository.create(run)


class StreamAgentRunService:
    def __init__(
        self,
        repository: AgentRunRepository,
        executor: AgentExecutor,
        tracer: Tracer,
    ) -> None:
        self._repository = repository
        self._executor = executor
        self._tracer = tracer

    async def execute(
        self,
        run: AgentRun,
        *,
        callbacks: list[Any] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        span = self._tracer.start_span("agent_run_stream", {"run_id": str(run.id)})
        run.mark_running()
        await self._repository.update(run)

        output: list[str] = []
        try:
            async for event in self._executor.astream(run.prompt, str(run.id), callbacks=callbacks):
                if token := event.get("token"):
                    output.append(token)
                yield event

            run.mark_completed("".join(output))
            await self._repository.update(run)
            self._tracer.end_span(span, status="ok")
            yield {"event": "done", "data": run.output_text}
        except Exception as exc:
            run.mark_failed(str(exc))
            await self._repository.update(run)
            self._tracer.end_span(span, status="error")
            yield {"event": "error", "data": str(exc)}
