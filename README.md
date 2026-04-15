# high_load_system_template

A production-ready template for building high-load, privacy-aware AI microservices using FastAPI, LangGraph, Redis, Celery, and self-hosted Langfuse.

## Architecture

This template enforces strict layer boundaries:

- `src/high_load_ai/api`: FastAPI routers, schemas, SSE/WebSocket endpoints.
- `src/high_load_ai/core`: config, DI composition, security, exceptions.
- `src/high_load_ai/domain`: pure business models, ports, and use cases.
- `src/high_load_ai/infrastructure`: SQLAlchemy repos, Redis limiter, Celery tasks, LLM adapter.
- `src/high_load_ai/ai`: isolated LangGraph state, prompts, graph, and runner.
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
