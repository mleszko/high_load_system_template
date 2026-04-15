# Correlation ID

## HTTP

- Clients may send **`X-Correlation-ID`**. If omitted, the server generates a UUID.
- The response echoes the same header.

## Context propagation

- **`core.context.correlation_id_var`** holds the ID for the current async task.
- **Logging** — every log line includes `[cid=...]` when logging is configured (see app lifespan).

## Celery

- Tasks should accept an optional **`correlation_id`** keyword argument.
- **`task_prerun`** restores correlation ID into context so worker logs match the API request.
- Example: `finalize_run.delay(run_id, correlation_id=...)`

## FastAPI BackgroundTasks

Use **`schedule_background_with_correlation`** from `core.correlation_propagation` so sync tasks run with the same correlation ID.

## WebSockets

Pass **`X-API-Key`** and optionally **`X-Correlation-ID`** in the WebSocket handshake headers (see [security-auth.md](../api/security-auth.md)).

## Langfuse / LangChain

Runnable metadata includes **`correlation_id`** and **`langfuse_session_id`** (run id) where tracing is enabled.
