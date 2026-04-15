# Security and authentication

## API key

HTTP routes use **`X-API-Key`** or **`Authorization: Bearer <key>`**.

Keys are listed in **`API_KEYS`** (comma-separated).

## WebSockets

The WebSocket handler validates the same credentials from **connection headers**:

- `X-API-Key`
- `Authorization: Bearer ...`

Unauthenticated connections are closed with an appropriate code before streaming.

## Correlation

Optional **`X-Correlation-ID`** on HTTP and WebSocket for tracing.

## Production

- Rotate keys via secrets manager.
- Terminate TLS at the edge (ingress / reverse proxy).
- Do not log raw API keys or full prompts if policy requires redaction.
