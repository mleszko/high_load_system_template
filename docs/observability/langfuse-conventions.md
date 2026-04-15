# Langfuse conventions (self-hosted)

## Environment

- `LANGFUSE_HOST` — base URL of your self-hosted instance
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`
- `TRACING_ENABLED=true`

## Metadata keys

LangChain callbacks receive metadata such as:

| Key | Description |
|-----|-------------|
| `langfuse_session_id` | Agent run id (ties traces to a run) |
| `correlation_id` | Cross-service request id |

Extend with `cache_hit`, `fallback_used`, `breaker_phase` as you harden observability.

## Privacy

Keep prompts and PII policies in your Langfuse project settings; this template does not ship external SaaS telemetry.
