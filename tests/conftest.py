from __future__ import annotations

import os

import fakeredis.aioredis
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("TRACING_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("API_KEYS", "local-dev-key")

from high_load_ai.core.config import Settings
from high_load_ai.core.container import Container
from high_load_ai.domain.ports import AgentExecutor, AgentRunRepository, RateLimiter, Tracer
from high_load_ai.infrastructure.db.models import Base
from high_load_ai.infrastructure.rate_limiters.redis_rate_limiter import RedisRateLimiter
from high_load_ai.infrastructure.repositories.sqlalchemy_runs import SqlAlchemyAgentRunRepository
from high_load_ai.infrastructure.tracing import NoopTracer


@pytest.fixture
def test_container() -> Container:
    settings = Settings()
    redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

    engine = create_async_engine(settings.database_url, connect_args={"check_same_thread": False})
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    import asyncio

    async def _init_db() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init_db())

    run_repository: AgentRunRepository = SqlAlchemyAgentRunRepository(session_factory)
    rate_limiter: RateLimiter = RedisRateLimiter(redis_client)

    from high_load_ai.ai.runner import LangGraphExecutor
    from high_load_ai.infrastructure.llm.stub import StubLlmExecutor

    llm_executor: AgentExecutor = StubLlmExecutor()
    graph_executor: AgentExecutor = LangGraphExecutor(llm_executor)
    tracer: Tracer = NoopTracer()

    return Container(
        settings=settings,
        redis=redis_client,
        session_factory=session_factory,
        run_repository=run_repository,
        rate_limiter=rate_limiter,
        llm_executor=llm_executor,
        graph_executor=graph_executor,
        tracer=tracer,
    )


@pytest.fixture(autouse=True)
def _patch_build_container(monkeypatch: pytest.MonkeyPatch, test_container: Container) -> None:
    monkeypatch.setattr("high_load_ai.main.build_container", lambda: test_container)
