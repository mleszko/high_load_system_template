# Operational limits

| Concern | Setting | Default (example) |
|---------|---------|-------------------|
| Prompt max length | Pydantic schema | 16_000 chars |
| Rate limit | `RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | 60 / 60 |
| Primary LLM timeout | `LLM_TIMEOUT_SECONDS` | 45 |
| Fallback timeout | `LLM_FALLBACK_TIMEOUT_SECONDS` | 30 |
| Exact cache TTL | `EXACT_RUN_CACHE_TTL_SECONDS` | 30 |
| GZip minimum | `GZIP_MINIMUM_SIZE` | 1000 bytes |

Tune per environment. SSE streams are often small per chunk; gzip mainly helps large JSON responses.
