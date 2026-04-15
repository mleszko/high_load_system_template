# Local runbook

## Start stack

```bash
docker compose up --build
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Langfuse: http://localhost:3001  

## Migrations

```bash
alembic upgrade head
```

## Common env toggles

- `LLM_STUB=true` — deterministic stub model
- `SEMANTIC_CACHE_ENABLED=true` — semantic cache (use `hash` mode locally)
- `TRACING_ENABLED=false` — disable Langfuse client
- Tight rate limits for testing: `RATE_LIMIT_MAX_REQUESTS=5`

## Logs

Correlation ID appears as `[cid=...]` when the app configures logging on startup.
