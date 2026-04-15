# Streaming contract (SSE / WebSocket)

## REST

- `POST /v1/runs` — body `{"prompt": string}`; returns `{"run_id": uuid}`.
- `GET /v1/runs/{run_id}` — run status snapshot.
- `GET /v1/runs/{run_id}/stream` — **SSE** (`text/event-stream`).

## SSE event types

Payloads are JSON strings in the `data` field (except raw token text may be wrapped as `{"text": "..."}` from the router).

| Event | Meaning |
|-------|---------|
| `progress` | Milestone string (e.g. graph started, cache hit/miss) |
| `token` | Incremental model output chunk |
| `cached` | Full text served from semantic cache |
| `done` | Run completed; data contains final output |
| `error` | Failure message |

## WebSocket

`WS /v1/runs/{run_id}/ws` emits **JSON objects** with keys `event`, `data`, `token` mirroring the internal event dict.

**Auth:** send `X-API-Key` (and optional `X-Correlation-ID`) in the WebSocket handshake headers.

## Limits

See [operational-limits.md](./operational-limits.md).
