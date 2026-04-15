from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

from high_load_ai.api.middleware.correlation import CorrelationIdMiddleware
from high_load_ai.api.routers.runs import router as runs_router
from high_load_ai.core.config import get_settings
from high_load_ai.core.container import build_container
from high_load_ai.core.logging_config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    container = build_container()
    app.state.container = container
    try:
        yield
    finally:
        await container.redis.aclose()


settings = get_settings()
app = FastAPI(title="high_load_system_template", lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(runs_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
