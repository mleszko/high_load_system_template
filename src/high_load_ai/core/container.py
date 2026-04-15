from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langfuse import Langfuse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from high_load_ai.ai.runner import LangGraphExecutor
from high_load_ai.core.config import Settings, get_settings
from high_load_ai.domain.ports import AgentExecutor, AgentRunRepository, RateLimiter, Tracer
from high_load_ai.infrastructure.db.session import build_session_factory
from high_load_ai.infrastructure.llm.openai_compatible import OpenAICompatibleClient
from high_load_ai.infrastructure.llm.stub import StubLlmExecutor
from high_load_ai.infrastructure.rate_limiters.redis_rate_limiter import RedisRateLimiter
from high_load_ai.infrastructure.repositories.sqlalchemy_runs import SqlAlchemyAgentRunRepository
from high_load_ai.infrastructure.tracing import LangfuseTracer, NoopTracer


@dataclass(frozen=True)
class Container:
    settings: Settings
    redis: Redis
    session_factory: async_sessionmaker[AsyncSession]
    run_repository: AgentRunRepository
    rate_limiter: RateLimiter
    llm_executor: AgentExecutor
    graph_executor: AgentExecutor
    tracer: Tracer


def build_container() -> Container:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    session_factory = build_session_factory(settings)
    run_repository = SqlAlchemyAgentRunRepository(session_factory)
    rate_limiter = RedisRateLimiter(redis)
    llm_executor: AgentExecutor
    if settings.llm_stub_enabled:
        llm_executor = StubLlmExecutor()
    else:
        llm_executor = OpenAICompatibleClient(settings)
    graph_executor = LangGraphExecutor(llm_executor)

    tracer: Tracer = NoopTracer()
    if settings.langfuse_enabled:
        client = Langfuse(
            host=settings.langfuse_host,
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
        )
        tracer = LangfuseTracer(client)

    return Container(
        settings=settings,
        redis=redis,
        session_factory=session_factory,
        run_repository=run_repository,
        rate_limiter=rate_limiter,
        llm_executor=llm_executor,
        graph_executor=graph_executor,
        tracer=tracer,
    )


def build_langchain_callbacks(tracer: Tracer) -> list[Any]:
    callback_factory = getattr(tracer, "callback_handler", None)
    if callable(callback_factory):
        return [callback_factory()]
    return []
