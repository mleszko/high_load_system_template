# CI load tests

The workflow **`.github/workflows/load-tests.yml`** runs **k6** against a configurable base URL.

## Usage

1. In GitHub: **Actions → Load tests (k6) → Run workflow**.
2. Inputs:
   - `base_url` — e.g. staging deployment
   - `api_key` — use a GitHub secret in real environments

## Requirements

The job installs k6 from Grafana’s apt repo and runs `tests/load/k6-sse.js`. Adjust the workflow to add `k6-rate-limit.js` or gates as needed.

**Security:** do not commit real API keys; pass them via repository secrets.
