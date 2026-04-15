# Clean architecture boundaries

## Allowed dependencies

- **`domain`** may import only the standard library and typing helpers. No FastAPI, SQLAlchemy, Redis, LangGraph, or LLM SDKs.
- **`api`** may import `domain`, `core`, and infrastructure only through the **container** and explicit adapters (no deep ORM in routers).
- **`infrastructure`** implements ports defined in `domain` (or used by `core` composition) and may use databases, Redis, HTTP, Celery.
- **`ai`** contains LangGraph and caching/breaker logic. It must not import FastAPI. It uses **`AgentExecutor`**-shaped callables injected from composition.

## Caching and resilience placement

- **Exact (Redis) cache** for read models lives in **`infrastructure`**; routers decide when to read/write.
- **Semantic LLM cache** and **circuit breaker / fallback** live in **`ai`** so provider-specific behavior stays isolated.
- **Correlation ID** is a cross-cutting concern: **`api` middleware** sets context; **`core.context`** holds it; workers restore it from task kwargs.
