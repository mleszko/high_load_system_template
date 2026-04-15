from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=16_000)


class CreateRunResponse(BaseModel):
    run_id: str


class RunResponse(BaseModel):
    run_id: str
    status: str
    output_text: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
