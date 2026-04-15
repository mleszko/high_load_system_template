from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langfuse import Langfuse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from high_load_ai.ai.circuit_breaker import CircuitBreakerState
from high_load_ai.ai.resilient_llm import ResilientLlmExecutor
from high_load_ai.ai.runner import LangGraphExecutor
from high_load_ai.ai.semantic_cache import SemanticLlmCache
from high_load_ai.core.config import Settings, get_settings
from high_load_ai.domain.ports import AgentExecutor, AgentRunRepository, RateLimiter, Tracer
from high_load_ai.infrastructure.cache.exact_run_cache import ExactRunCache
from high_load_ai.infrastructure.db.session import build_session_factory
from high_load_ai.infrastructure.llm.openai_model import OpenAIModelClient
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
    exact_run_cache: ExactRunCache | None
    llm_executor: AgentExecutor
    graph_executor: AgentExecutor
    tracer: Tracer


def build_container() -> Container:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    session_factory = build_session_factory(settings)
    run_repository = SqlAlchemyAgentRunRepository(session_factory)
    rate_limiter = RedisRateLimiter(redis)

    exact_run_cache: ExactRunCache | None = None
    if settings.exact_cache_enabled:
        exact_run_cache = ExactRunCache(
            redis,
            ttl_seconds=settings.exact_run_cache_ttl_seconds,
        )

    semantic_cache = SemanticLlmCache(redis, settings)

    llm_executor: AgentExecutor
    if settings.llm_stub_enabled:
        llm_executor = StubLlmExecutor()
    else:
        primary = OpenAIModelClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        fallback = OpenAIModelClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_fallback_model,
            timeout_seconds=settings.llm_fallback_timeout_seconds,
        )
        breaker = CircuitBreakerState(
            fail_max=settings.circuit_breaker_fail_max,
            reset_timeout_seconds=settings.circuit_breaker_reset_seconds,
        )
        llm_executor = ResilientLlmExecutor(primary, fallback, breaker)

    graph_executor = LangGraphExecutor(llm_executor, semantic_cache)

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
        exact_run_cache=exact_run_cache,
        llm_executor=llm_executor,
        graph_executor=graph_executor,
        tracer=tracer,
    )


def build_langchain_callbacks(tracer: Tracer) -> list[Any]:
    callback_factory = getattr(tracer, "callback_handler", None)
    if callable(callback_factory):
        return [callback_factory()]
    return []
