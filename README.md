# high_load_system_template

A production-ready template for building high-load, privacy-aware AI microservices using FastAPI, LangGraph, Redis, Celery, and self-hosted Langfuse.

## Documentation

Full guides: **[docs/README.md](docs/README.md)** (architecture, caching, reliability, observability, API contract, load testing, runbooks).

## Architecture

This template enforces strict layer boundaries:

- `src/high_load_ai/api`: FastAPI routers, schemas, SSE/WebSocket endpoints.
- `src/high_load_ai/core`: config, DI composition, security, exceptions.
- `src/high_load_ai/domain`: pure business models, ports, and use cases.
- `src/high_load_ai/infrastructure`: SQLAlchemy repos, Redis limiter, Celery tasks, LLM adapter.
- `src/high_load_ai/ai`: isolated LangGraph state, prompts, graph, runner, **semantic LLM cache**, **circuit breaker** + fallback wiring.
- `deploy`: Azure Bicep templates for Container Apps.
- `client`: Next.js TypeScript streaming demo client.

## Local development

### Prerequisites

- Python 3.11+
- Docker + Docker Compose
- Node.js 20+ (for client)

### Run full local stack

```bash
docker compose up --build
```

Services:

- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Langfuse UI (self-hosted): http://localhost:3001
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Run API without Docker (optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn high_load_ai.main:app --reload --host 0.0.0.0 --port 8000
```

### Database migration

```bash
alembic upgrade head
```

## Quality checks

```bash
ruff check /workspace/src /workspace/tests
mypy --config-file /workspace/pyproject.toml
pytest
```

## Caching, resilience, and tracing

- **Exact Redis cache**: `GET /v1/runs/{id}` uses a short-TTL Redis cache when `EXACT_CACHE_ENABLED=true` (default). Streaming invalidates the cache for that run.
- **Semantic LLM cache**: enable with `SEMANTIC_CACHE_ENABLED=true`. Default embedding mode is deterministic `hash` (no external calls). Set `SEMANTIC_CACHE_EMBED_MODE=openai` to use OpenAI-compatible embeddings via `LLM_BASE_URL` / `LLM_API_KEY`.
- **Circuit breaker + fallback**: primary model `LLM_MODEL` with fallback `LLM_FALLBACK_MODEL` (same API base by default). Tune `CIRCUIT_BREAKER_FAIL_MAX` and `CIRCUIT_BREAKER_RESET_SECONDS`.
- **Correlation ID**: send `X-Correlation-ID` or receive one in the response; included in logs (`[cid=...]`) and passed to Celery `finalize_run`. LangChain callbacks receive `correlation_id` in metadata when tracing is enabled.
- **GZip**: `GZipMiddleware` compresses responses over `GZIP_MINIMUM_SIZE` bytes (SSE streams are typically small / event-based).

## Load testing

See [docs/performance/load-testing.md](docs/performance/load-testing.md) and `tests/load/README.md` for **k6** and **Locust** (including rate-limit scenarios).

## API quickstart

Create run:

```bash
curl -X POST "http://localhost:8000/v1/runs" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{"prompt":"Explain bounded concurrency under high load"}'
```

Stream run events (SSE):

```bash
curl -N "http://localhost:8000/v1/runs/<run_id>/stream" \
  -H "X-API-Key: dev-key"
```

## Client demo

```bash
cd /workspace/client
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` if your API is not at `http://localhost:8000`.

## Notes on privacy and observability

- Observability is designed for self-hosted Langfuse only.
- Do not commit production secrets; use env vars and/or secret managers.
- Tracing is enabled when `TRACING_ENABLED=true` and Langfuse keys are configured.

## Azure deployment

See full commands and parameters in:

- `/workspace/deploy/main.bicep`
- `/workspace/deploy/README.md`
