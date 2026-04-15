from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketException, status
from sse_starlette import EventSourceResponse

from high_load_ai.api.dependencies import enforce_rate_limit, get_container
from high_load_ai.api.schemas.runs import CreateRunRequest, CreateRunResponse, RunResponse
from high_load_ai.core.container import Container, build_langchain_callbacks
from high_load_ai.domain.services import StartAgentRunService, StreamAgentRunService
from high_load_ai.infrastructure.tasks.tasks import finalize_run

router = APIRouter(prefix="/v1/runs", tags=["runs"])


@router.post("", response_model=CreateRunResponse, dependencies=[Depends(enforce_rate_limit)])
async def create_run(
    payload: CreateRunRequest,
    container: Container = Depends(get_container),
) -> CreateRunResponse:
    service = StartAgentRunService(container.run_repository)
    run = await service.execute(payload.prompt)
    return CreateRunResponse(run_id=str(run.id))


@router.get("/{run_id}", response_model=RunResponse, dependencies=[Depends(enforce_rate_limit)])
async def get_run(
    run_id: str,
    container: Container = Depends(get_container),
) -> RunResponse:
    run = await container.run_repository.get(UUID(run_id))
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RunResponse(
        run_id=str(run.id),
        status=run.status.value,
        output_text=run.output_text,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.get("/{run_id}/stream", dependencies=[Depends(enforce_rate_limit)])
async def stream_run(
    run_id: str,
    container: Container = Depends(get_container),
) -> EventSourceResponse:
    run = await container.run_repository.get(UUID(run_id))
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    service = StreamAgentRunService(container.run_repository, container.graph_executor, container.tracer)
    callbacks = build_langchain_callbacks(container.tracer)

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        async for event in service.execute(run, callbacks=callbacks):
            data = event.get("data") or event.get("token", "")
            yield {"event": event.get("event", "progress"), "data": json.dumps({"text": data})}
        if container.settings.background_tasks_enabled:
            finalize_run.delay(str(run.id))

    return EventSourceResponse(event_generator())


@router.websocket("/{run_id}/ws")
async def stream_run_ws(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    container: Container = websocket.app.state.container  
    run = await container.run_repository.get(UUID(run_id))
    if run is None:
        await websocket.close(code=1008)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    service = StreamAgentRunService(container.run_repository, container.graph_executor, container.tracer)
    callbacks = build_langchain_callbacks(container.tracer)
    async for event in service.execute(run, callbacks=callbacks):
        await websocket.send_json(event)
    await websocket.close()
