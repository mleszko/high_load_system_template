# Load tests

Stress the API (especially **SSE** and **rate limits**) using **k6** or **Locust**.

## Prerequisites

- API running (e.g. `docker compose up` → `http://localhost:8000`).
- Valid `X-API-Key` (compose default: `dev-key`).
- For high volume, consider `LLM_STUB=true` or a fast local model so the LLM is not the bottleneck.

## k6

```bash
k6 run tests/load/k6-sse.js \
  -e BASE_URL=http://localhost:8000 \
  -e API_KEY=dev-key
```

## Locust

```bash
pip install locust
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Set `API_KEY` in the Locust UI or export `LOCUST_API_KEY=dev-key` and adjust `locustfile` if you wire env reading.

## What is exercised

- `POST /v1/runs` + `GET /v1/runs/{id}/stream` (k6 opens the stream; body may be buffered depending on client).
- Optional: send `X-Correlation-ID` header to verify tracing propagation in logs.
