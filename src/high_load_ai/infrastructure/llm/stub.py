from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any


class StubLlmExecutor:
    async def astream(
        self,
        prompt: str,
        run_id: str,
        *,
        callbacks: list[Any] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        _ = callbacks
        yield {"event": "progress", "data": f"run={run_id}:stub_started"}
        for word in prompt.split():
            yield {"event": "token", "token": f"{word} "}
        yield {"event": "progress", "data": f"run={run_id}:stub_completed"}
