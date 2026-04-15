from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from high_load_ai.api.routers.runs import router as runs_router
from high_load_ai.core.container import build_container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container = build_container()
    app.state.container = container
    try:
        yield
    finally:
        await container.redis.aclose()


app = FastAPI(title="high_load_system_template", lifespan=lifespan)
app.include_router(runs_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
