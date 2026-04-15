from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from high_load_ai.ai.graph import build_graph
from high_load_ai.ai.semantic_cache import SemanticLlmCache
from high_load_ai.domain.ports import AgentExecutor


class LangGraphExecutor(AgentExecutor):
    def __init__(self, llm_executor: AgentExecutor, semantic_cache: SemanticLlmCache | None = None) -> None:
        self._graph = build_graph(llm_executor).compile()
        self._llm_executor = llm_executor
        self._semantic_cache = semantic_cache

    async def astream(
        self,
        prompt: str,
        run_id: str,
        *,
        callbacks: list[Any] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        yield {"event": "progress", "data": "graph:started"}

        final_text: str | None = None

        if self._semantic_cache and self._semantic_cache.enabled():
            cached = await self._semantic_cache.lookup(prompt)
            if cached is not None:
                yield {"event": "progress", "data": "semantic_cache:hit"}
                yield {"event": "cached", "data": cached}
                final_text = cached
                for word in cached.split():
                    yield {"event": "token", "token": f"{word} "}
            else:
                yield {"event": "progress", "data": "semantic_cache:miss"}

        if final_text is None:
            parts: list[str] = []
            async for event in self._llm_executor.astream(prompt, run_id, callbacks=callbacks):
                yield event
                if token := event.get("token"):
                    parts.append(token)
            final_text = "".join(parts)
            if self._semantic_cache and self._semantic_cache.enabled():
                await self._semantic_cache.store(prompt, final_text)

        _ = await self._graph.ainvoke(
            {
                "prompt": prompt,
                "run_id": run_id,
                "callbacks": callbacks or [],
                "response": final_text or "",
            }
        )
        yield {"event": "progress", "data": "graph:completed"}
