# Exact (Redis) cache

## Scope

Caches **`GET /v1/runs/{run_id}`** responses for a short TTL to cut database read load under high churn.

## Key format

Keys are **`cache:run:{run_id}`** (plus optional prefix in code). For multi-tenant extensions, evolve to:

`cache:v1:runs:{tenant}:{run_id}`

## Invalidation

- **On stream start** — cache entry for that `run_id` is deleted when streaming begins.
- **After stream completes or errors** — cache is deleted again so the next GET reflects final state.

## Configuration

| Variable | Default |
|----------|---------|
| `EXACT_CACHE_ENABLED` | `true` |
| `EXACT_RUN_CACHE_TTL_SECONDS` | `30` |

## Safety

Do not cache responses that include secrets. Run DTOs are status + prompt output only.
