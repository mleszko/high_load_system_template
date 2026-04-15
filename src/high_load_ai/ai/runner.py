from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from high_load_ai.ai.graph import build_graph
from high_load_ai.domain.ports import AgentExecutor


class LangGraphExecutor(AgentExecutor):
    def __init__(self, llm_executor: AgentExecutor) -> None:
        self._graph = build_graph(llm_executor).compile()
        self._llm_executor = llm_executor

    async def astream(
        self,
        prompt: str,
        run_id: str,
        *,
        callbacks: list[Any] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        yield {"event": "progress", "data": "graph:started"}

        # Keep token streaming path fast and direct for API consumers.
        async for event in self._llm_executor.astream(prompt, run_id, callbacks=callbacks):
            yield event

        _ = await self._graph.ainvoke({"prompt": prompt, "run_id": run_id, "callbacks": callbacks or []})
        yield {"event": "progress", "data": "graph:completed"}
