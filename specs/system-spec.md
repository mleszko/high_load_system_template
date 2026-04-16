# system-spec.md (spec-kit)

**Status**: Active (source of truth)  
**Spec Version**: 1.0.0  
**Applies to**: `high_load_system_template` (FastAPI + LangGraph + Redis/Celery + Postgres)

---

## 0) Purpose

This document defines the **data contracts** between:

- **FastAPI layer** (`src/high_load_ai/api`)
- **AI/LangGraph layer** (`src/high_load_ai/ai`)
- **Infrastructure layer** (`src/high_load_ai/infrastructure`)

It is the **source of truth** for future features. Any change to a contract must update this spec first (or in the same PR).

---

## 1) Contract rules

### 1.1 Stability & versioning

- API routes are versioned under `/v1/...`.
- **Breaking changes** require either:
  - a new route version (e.g. `/v2`), or
  - backward compatible behavior (additive changes only).
- Storage contracts (DB schemas, Redis keys) are **append-only** where possible; destructive changes require migrations.

### 1.2 Cross-layer coupling

- `domain/` must not depend on FastAPI, Redis clients, LangGraph, or SQLAlchemy.
- `api/` may only use infrastructure via the **container** (`core/container.py`) and DTOs.
- `ai/` must not import FastAPI.

### 1.3 Correlation ID propagation (distributed tracing)

- Header: `X-Correlation-ID`.
- If missing, server generates a UUID.
- The correlation id must be:
  - emitted back in HTTP responses,
  - available in request context (`core.context`),
  - passed to Celery tasks as `correlation_id`,
  - attached to LLM invocation metadata (LangChain callbacks) when tracing is enabled.

---

## 2) Domain contracts

### 2.1 Entity: `AgentRun`

**Canonical fields** (domain-level):

- `id`: UUID (`RunId` wrapper)
- `prompt`: string
- `status`: `pending|running|completed|failed`
- `output_text`: string
- `error_message`: string | null
- `created_at`, `updated_at`: timezone-aware UTC datetimes

**Status transitions**:

- `pending → running → completed`
- `pending → running → failed`

---

## 3) API contracts (FastAPI)

### 3.1 Authentication

- HTTP requests must include:
  - `X-API-Key: <key>` **or**
  - `Authorization: Bearer <key>`
- Keys are configured in `API_KEYS` (comma-separated).

### 3.2 REST endpoints

#### 3.2.1 Create run

- **Route**: `POST /v1/runs`
- **Request JSON**:

```json
{ "prompt": "string (1..16000)" }
```

- **Response JSON**:

```json
{ "run_id": "uuid" }
```

#### 3.2.2 Get run snapshot

- **Route**: `GET /v1/runs/{run_id}`
- **Response JSON**:

```json
{
  "run_id": "uuid",
  "status": "pending|running|completed|failed",
  "output_text": "string",
  "error_message": "string|null",
  "created_at": "RFC3339 datetime",
  "updated_at": "RFC3339 datetime"
}
```

**Caching**: may be served from exact Redis cache (`ExactRunCache`) when enabled.

#### 3.2.3 Stream run (SSE)

- **Route**: `GET /v1/runs/{run_id}/stream`
- **Content-Type**: `text/event-stream`

##### SSE event envelope

Each SSE message is emitted as:

- `event: <event_name>`
- `data: <json_string>`

The **data** field is always JSON:

```json
{ "text": "..." }
```

##### SSE events

| Event | Meaning | Data.text |
|------:|---------|-----------|
| `progress` | milestone | human-readable string |
| `token` | incremental output | token chunk |
| `cached` | semantic cache hit (full text) | full cached output |
| `done` | completion | final output |
| `error` | failure | error string |

**Notes**:

- `cached` may occur before tokens; tokens may then stream the cached output for UI parity.
- `progress` includes at least: `graph:started`, `graph:completed`, and `semantic_cache:hit|miss` when semantic cache enabled.

#### 3.2.4 Stream run (WebSocket)

- **Route**: `WS /v1/runs/{run_id}/ws`
- **Auth**: same as HTTP, via handshake headers (`X-API-Key` or `Authorization`).

##### WS message envelope

Server sends JSON objects of the internal event dict:

```json
{ "event": "progress|token|cached|done|error", "data": "...", "token": "..." }
```

- `data` and/or `token` may appear depending on event type.

---

## 4) AI contracts (LangGraph + executor)

### 4.1 LangGraph state: `AgentGraphState`

This is the canonical state contract between the executor and LangGraph.

```json
{
  "run_id": "string (uuid)",
  "prompt": "string",
  "response": "string",
  "callbacks": "list (opaque callback objects)"
}
```

Rules:

- `response` is **optional**. If present, the graph must treat it as authoritative output and must not re-invoke the model.
- `callbacks` is opaque and may be empty.

### 4.2 Executor stream contract: `AgentExecutor.astream`

The AI executor yields an async stream of **event dicts**:

```json
{ "event": "progress|token|cached|done|error", "data": "...", "token": "..." }
```

Rules:

- Token streaming uses `{"event":"token","token":"..."}`.
- Milestones use `{"event":"progress","data":"..."}`.
- A semantic cache hit emits `{"event":"cached","data":"<full text>"}`.

### 4.3 Semantic cache contract

- **Enabled by**: `SEMANTIC_CACHE_ENABLED=true` and `LLM_STUB=false`.
- **Embedding modes**:
  - `SEMANTIC_CACHE_EMBED_MODE=hash` (deterministic pseudo-embeddings)
  - `SEMANTIC_CACHE_EMBED_MODE=openai` (OpenAI-compatible embeddings)

On hit:

- executor must emit:
  - `progress semantic_cache:hit`
  - `cached <full text>`
  - token stream mirroring the cached text (UI convenience)

On miss:

- executor emits `progress semantic_cache:miss` and continues with live LLM.

---

## 5) Infrastructure contracts

### 5.1 PostgreSQL schema contract

Table: `agent_runs`

| Column | Type | Notes |
|--------|------|------|
| `id` | `varchar(36)` | UUID string primary key |
| `prompt` | `text` | original prompt |
| `status` | `varchar(32)` | one of domain statuses |
| `output_text` | `text` | default empty |
| `error_message` | `text nullable` | failure reason |
| `created_at` | `timestamptz` | UTC |
| `updated_at` | `timestamptz` | UTC |

Repository mapping must be bijective:

- `AgentRunModel ↔ AgentRun`

### 5.2 Redis key contracts

#### 5.2.1 Rate limit keys

Key pattern:

- `ratelimit:{api_key}:{route_path}`

Values:

- counter integer (`INCR`)
- TTL set to `RATE_LIMIT_WINDOW_SECONDS`

#### 5.2.2 Exact cache keys

Key pattern:

- `cache:run:{run_id}`

Value:

- JSON encoded `RunResponse` payload

TTL:

- `EXACT_RUN_CACHE_TTL_SECONDS`

Invalidation:

- Must delete cache entry when a run transitions through streaming updates.

#### 5.2.3 Semantic cache keys (bucketed)

Key pattern:

- `sem:llm:bkt:{bucket}`

Value entries:

```json
{ "vec": [float...], "text": "string" }
```

Bucket computation:

- derived from embedding vector; number of buckets determined by `SEMANTIC_CACHE_BUCKET_BITS`.

Each bucket list is capped to `max_entries_per_bucket` (currently 200).

### 5.3 Celery task contracts

Task: `high_load_ai.finalize_run`

Signature:

```python
finalize_run(run_id: str, correlation_id: str | None = None) -> str
```

Rules:

- If `correlation_id` is passed, worker must restore it into context for logging.

---

## 6) Observability contracts

### 6.1 Logging

- Every log record must include correlation id as `[cid=...]` (or `-` if missing).

### 6.2 Langfuse (self-hosted)

When tracing is enabled (`TRACING_ENABLED=true` and Langfuse keys set):

- LLM invocation metadata must include:
  - `langfuse_session_id` = run id
  - `correlation_id` = correlation id
  - `breaker_phase` = `closed|open|half_open`

---

## 7) Change control checklist

When adding a feature:

1. Update this spec: new/changed contracts (API, events, state, storage keys).
2. Add/adjust tests for contract compliance.
3. Ensure backward compatibility (or bump version / route).
4. Update docs under `docs/` if behavior is user-facing.

