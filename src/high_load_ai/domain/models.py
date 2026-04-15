from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class RunId:
    value: UUID

    @classmethod
    def new(cls) -> RunId:
        return cls(value=uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class AgentRun:
    id: RunId
    prompt: str
    status: RunStatus = RunStatus.PENDING
    output_text: str = ""
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def mark_running(self) -> None:
        self.status = RunStatus.RUNNING
        self.updated_at = datetime.now(tz=UTC)

    def mark_completed(self, output_text: str) -> None:
        self.status = RunStatus.COMPLETED
        self.output_text = output_text
        self.error_message = None
        self.updated_at = datetime.now(tz=UTC)

    def mark_failed(self, error_message: str) -> None:
        self.status = RunStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now(tz=UTC)
