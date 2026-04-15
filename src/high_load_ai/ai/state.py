from __future__ import annotations

from typing import Any, TypedDict


class AgentGraphState(TypedDict, total=False):
    run_id: str
    prompt: str
    response: str
    callbacks: list[Any]
