# Azure deployment (Container Apps)

This folder contains Bicep templates for deploying the API and worker to Azure Container Apps.

## Prerequisites

- Azure CLI installed and logged in.
- Existing resource group.
- Container image(s) already pushed to ACR or another registry accessible by Container Apps.

## Deploy

```bash
az deployment group create \
  --resource-group <rg-name> \
  --template-file /workspace/deploy/main.bicep \
  --parameters \
    namePrefix=hloadai \
    apiImage=<registry>/high-load-ai:latest \
    workerImage=<registry>/high-load-ai:latest \
    databaseUrl='postgresql+asyncpg://...' \
    redisUrl='redis://...' \
    celeryBrokerUrl='redis://.../1' \
    celeryResultBackend='redis://.../2' \
    apiKeys='prod-key-1,prod-key-2' \
    llmApiKey='<secret>'
```

For production, migrate secret values to Key Vault references in Bicep and remove raw secret parameter usage.

## Cost-safe Azure checklist (MVP / staging)

Use this checklist to keep deployment close to free/low-cost while testing.

1. Azure setup
   - `az login`
   - Create/select a dedicated RG (for easy cleanup), e.g. `rg-highload-dev`.

2. Cost guardrails (required)
   - Configure **Budget + Cost Alerts** in Azure Cost Management before first deploy.
   - Set low thresholds (for example 5/10/20 in your billing currency).

3. Container Apps sizing (minimal)
   - API app: `minReplicas=0`, `maxReplicas=1`, minimal CPU/RAM.
   - Worker app: `minReplicas=0`, `maxReplicas=1`, minimal CPU/RAM.
   - Keep concurrency conservative until load tests are done.

4. Runtime flags for cheap testing
   - Use `LLM_STUB=true` when possible (no paid model calls).
   - Keep `TRACING_ENABLED=false` initially; enable tracing only for short diagnostics.
   - If semantic cache is enabled in test mode, prefer `SEMANTIC_CACHE_EMBED_MODE=hash`.

5. Secrets and config
   - Store secrets in Key Vault (or secure secrets mechanism) as early as possible.
   - Never commit real API keys or provider credentials.

6. Smoke tests after deploy
   - `GET /health`
   - `POST /v1/runs`
   - SSE stream endpoint
   - WebSocket endpoint (with API key)

7. Short load test only
   - Run a short k6 scenario first (`tests/load/k6-sse.js`).
   - For rate-limit behavior, run `tests/load/k6-rate-limit.js` with tight limits.

8. Daily cost hygiene
   - Check daily cost for first week.
   - Scale down or delete environment when idle.
   - Keep non-prod resources in a dedicated RG for one-command cleanup.

## One-command cleanup (non-prod)

```bash
az group delete --name <rg-name> --yes --no-wait
```
