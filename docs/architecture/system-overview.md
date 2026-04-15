# System overview

The service is a **FastAPI** application with **Clean Architecture** layers:

- **`api/`** — HTTP routers, middleware (correlation ID, gzip), Pydantic DTOs, SSE and WebSocket.
- **`core/`** — configuration, dependency injection container, security, logging.
- **`domain/`** — entities, ports, and use cases (no framework imports).
- **`infrastructure/`** — PostgreSQL (SQLAlchemy async), Redis (rate limit, exact cache), Celery, LLM clients.
- **`ai/`** — LangGraph graph, semantic LLM cache, circuit breaker and resilient LLM execution.

Data flows: client → API → domain services → graph executor → LLM (with cache, breaker, fallback) → persistence and optional Celery finalize task.

See [clean-architecture-boundaries.md](./clean-architecture-boundaries.md) for dependency rules.
