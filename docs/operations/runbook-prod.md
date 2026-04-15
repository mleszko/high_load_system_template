# Production runbook (checklist)

## Before go-live

- [ ] Secrets from vault (DB, Redis, API keys, Langfuse), not `.env` in images
- [ ] `API_KEYS` rotated; least-privilege network from API to DB/Redis
- [ ] Langfuse self-hosted reachable only inside VPC
- [ ] Rate limits aligned with LLM provider quotas
- [ ] Breaker thresholds (`CIRCUIT_BREAKER_*`) tuned from staging incidents
- [ ] Semantic cache: embedding mode and similarity threshold validated for false positives
- [ ] Load tests (`tests/load/`) run against staging
- [ ] Alerts on error rate, latency p95, Celery queue depth, Redis memory

## Scaling

- Scale API replicas; ensure **sticky sessions not required** for stateless API
- Celery workers scale independently
- Redis: separate logical DBs or instances for cache vs broker if needed

## Rollback

- Keep previous container image tags; revert deployment and run DB migration rollback if any.
