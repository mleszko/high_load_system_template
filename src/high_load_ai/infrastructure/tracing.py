from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langfuse.langchain import CallbackHandler

from high_load_ai.domain.ports import Tracer


@dataclass
class SpanRef:
    name: str
    metadata: dict[str, str]


class NoopTracer(Tracer):
    def start_span(self, name: str, metadata: dict[str, str] | None = None) -> object:
        return SpanRef(name=name, metadata=metadata or {})

    def end_span(self, span: object, *, status: str) -> None:
        _ = span
        _ = status


class LangfuseTracer(Tracer):
    def __init__(self, client: Any) -> None:
        self._client = client

    def start_span(self, name: str, metadata: dict[str, str] | None = None) -> object:
        return self._client.start_as_current_observation(
            as_type="span",
            name=name,
            input=metadata or {},
        )

    def end_span(self, span: object, *, status: str) -> None:
        if hasattr(span, "update"):
            span.update(output={"status": status})

    def callback_handler(self) -> CallbackHandler:
        return CallbackHandler()
