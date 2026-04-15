# Load testing

## Scripts

| Script | Tool | Purpose |
|--------|------|---------|
| `tests/load/k6-sse.js` | k6 | Ramping VUs, POST + SSE |
| `tests/load/k6-rate-limit.js` | k6 | Burst traffic; expects some **429** when limits are tight |
| `tests/load/locustfile.py` | Locust | Python-native SSE smoke |

## Running locally

```bash
# Terminal 1
docker compose up --build

# Terminal 2 — optional: tight limits for 429 scenario
export RATE_LIMIT_MAX_REQUESTS=5
export RATE_LIMIT_WINDOW_SECONDS=60
# restart API with these env vars

k6 run tests/load/k6-sse.js -e BASE_URL=http://localhost:8000 -e API_KEY=dev-key
k6 run tests/load/k6-rate-limit.js -e BASE_URL=http://localhost:8000 -e API_KEY=dev-key
```

Use `LLM_STUB=true` or a fast local model so the LLM is not the bottleneck when testing API throughput.

## CI

See [ci-load-tests.md](./ci-load-tests.md). The GitHub workflow is **manual** (`workflow_dispatch`) by default.
