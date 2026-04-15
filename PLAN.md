# PLAN: high_load_system_template

This document is the authoritative implementation roadmap. **Implementation pauses until you type `continue` after each agreed batch of work.** (This revision updates the plan only; no feature code is implied until you approve execution.)

## Acknowledged additions (this revision)

The following are now **first-class requirements** for a production-grade, high-load system:

1. **Multi-level caching (cost & latency)**  
   - **Standard Redis cache**: deterministic keying for frequent, identical API requests (idempotent reads / safe responses only; document cache invalidation rules).  
   - **LLM semantic cache**: implemented **inside `/ai`** so semantically equivalent user queries return a cached LLM answer **before** invoking the graph or primary model—backed by Redis as a vector store or LangChain’s semantic cache pattern, without coupling `/domain` to Redis specifics.

2. **Advanced scaling & reliability (graceful degradation)**  
   - **Circuit breaker pattern** around LLM calls, with **automatic fallback** in the `/ai` layer: if the primary model fails (timeouts, 429, 5xx, breaker open), LangGraph routes to a **secondary, faster/cheaper** model. Breaker state must be observable in logs/traces.

3. **Distributed tracing & correlation**  
   - **Correlation ID middleware** in FastAPI: accept `X-Correlation-ID` or generate one; store on `request.state`.  
   - Propagate the correlation ID through **Celery tasks**, **Redis pub/sub or task headers**, and any **BackgroundTasks** so a single user request can be stitched across decoupled components.  
   - Inject the same ID into **self-hosted Langfuse** trace metadata (e.g. `langfuse_session_id` / custom metadata) and **structured logging** on API, worker, and `/ai` execution paths.

4. **Efficient data transfer**  
   - Enable **`GZipMiddleware`** (or equivalent Starlette gzip) for compressible responses where safe (respecting streaming/SSE constraints—SSE streams may remain uncompressed or use chunked patterns per framework limits; document behavior).

5. **Performance testing**  
   - Add **`tests/load/`** with a **k6** or **Locust** script targeting: sustained **SSE** connections, burst traffic on **rate-limited** routes, and basic POST/create load. Include README notes for running against local `docker compose` and CI opt-in.

## Guiding principles

- **Clean Architecture / DDD**: dependencies point inward. `/domain` stays free of FastAPI, Redis clients, LangGraph, and provider SDKs. Caching and circuit-breaker **policies** may appear as ports; **implementations** live in `/infrastructure` or `/ai` adapters as appropriate.
- **Privacy-by-default**: no external observability SaaS. Traces and logs go to **self-hosted Langfuse** and your log stack only.
- **High load & tail latency**: async I/O at the edge; offload non-latency-sensitive work; stream tokens; **cache** and **fallback** to protect p95/p99 under provider instability.
- **Resilience & cost**: retries (tenacity) + **circuit breaker** + **semantic cache** + Redis rate limits.

## Target repository layout (updated)

```text
high_load_system_template/
├── PLAN.md
├── pyproject.toml
├── README.md
├── docker-compose.yml
├── Dockerfile
├── deploy/
│   ├── main.bicep
│   ├── modules/
│   └── README.md
├── src/
│   └── high_load_ai/
│       ├── api/                 # Routers, middleware (correlation, gzip), schemas, SSE/WS
│       ├── core/              # Config, DI, exceptions, security
│       ├── domain/            # Entities, ports (incl. cache/breaker abstractions if needed)
│       ├── infrastructure/    # Redis cache repo, Celery, DB, LLM HTTP, tracing hooks
│       └── ai/                # LangGraph, semantic cache, circuit breaker + fallback routing
├── tests/
│   ├── unit/
│   ├── api/
│   └── load/                  # k6 or Locust scenarios + README
└── client/
```

## Architecture: caching & fallback (conceptual)

```mermaid
flowchart LR
  subgraph api [FastAPI_api]
    MW[CorrelationId_and_GZip_middleware]
    RL[Rate_limit]
  end
  subgraph ai [/ai_layer]
    SC[Semantic_cache_lookup]
    LG[LangGraph]
    CB[Circuit_breaker_primary]
    FB[Fallback_model]
  end
  subgraph infra [Infrastructure]
    RC[Redis_exact_cache]
    VS[Redis_vector_semantic_cache]
    LLM1[Primary_LLM]
    LLM2[Secondary_LLM]
  end

  MW --> RL
  RL --> SC
  SC -->|miss| LG
  SC -->|hit| api
  LG --> CB
  CB -->|ok| LLM1
  CB -->|open_or_fail| FB
  FB --> LLM2
  SC -.-> VS
  api -.-> RC
```

## Implementation phases (updated)

Phases **0–8** from the prior plan remain the backbone. The following **extends** them; when implementing, merge into the appropriate phase or add sub-deliverables.

### Phase A — Multi-level caching

- **Exact-match Redis cache** (infrastructure): cache key from normalized request fingerprint + API version + auth principal hash; TTL and invalidation documented; never cache authenticated streaming payloads unless explicitly safe.
- **Semantic LLM cache** (`/ai`): embed query (local or API per config), similarity search in Redis vector store or LangChain `RedisCache` / semantic cache integration; **on hit**, emit SSE `cached` event and skip provider call; **on miss**, run graph and **write-through** cache with metadata (model, temperature, correlation ID).
- Tests: unit tests for key normalization; integration test with **fake** embedding provider.

### Phase B — Circuit breaker & model fallback

- Implement breaker state (closed/open/half-open) with thresholds for failures, slow calls, and optional 429 handling; expose metrics via logs.
- `/ai` graph: primary node uses breaker-wrapped client; fallback node uses secondary model configuration from settings (`LLM_FALLBACK_*`).
- Domain/infrastructure boundary: breaker is not leaked into entities—keep behind `LlmInvocationPort` or similar.

### Phase C — Correlation ID & trace propagation

- FastAPI middleware: read/generate correlation ID; bind to contextvars; include in **every** log record (structlog or logging `Filter`).
- Celery: pass correlation ID in task kwargs or headers; worker sets context on task start.
- Langfuse: attach correlation ID to LangChain callback metadata / trace attributes for each run.
- BackgroundTasks: same context propagation utility as Celery.

### Phase D — GZip & payload efficiency

- Add Starlette/FastAPI gzip middleware with sensible minimum size threshold; document interaction with SSE (typically excluded or special-cased).

### Phase E — Load testing

- `tests/load/`:  
  - **k6** script: ramping VUs, SSE endpoint duration, rate-limit 429 verification.  
  - **or Locust**: Python-native, easier LLM stub environments.  
- Document `docker compose` target host, required API keys, and env toggles (`LLM_STUB`, cache on/off).

## Testing strategy (additions)

- **Load tests** are not gatekeepers for unit CI by default; run nightly or on `workflow_dispatch`.
- **Chaos-lite**: optional pytest that forces breaker open and asserts fallback path with stub LLM.

## Open decisions (defaults for implementation)

- **Semantic cache embedding**: pluggable—local small model vs provider embeddings; must work air-gapped if `EMBEDDING_PROVIDER=local`.
- **k6 vs Locust**: ship **one** primary script (default **k6** for SSE) plus a short note for the alternative.
- **Exact cache scope**: start with `GET /v1/runs/{id}` and safe read models; expand only with explicit cache headers.

---

## Execution contract

1. Updates to this `PLAN.md` are complete with this revision.  
2. **No implementation code** will be written until you send **`continue`**.  
3. After `continue`, work proceeds in **small batches** (cache → breaker → correlation → gzip → load tests), with commits per batch.
