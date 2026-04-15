# Circuit breaker

## Behavior

The template uses a **three-phase** breaker on the **primary** LLM path:

1. **Closed** — requests use the primary model. Consecutive failures increment a counter; when it reaches `CIRCUIT_BREAKER_FAIL_MAX`, the breaker **opens**.
2. **Open** — the primary is skipped; traffic uses the **fallback** model only until `CIRCUIT_BREAKER_RESET_SECONDS` elapses.
3. **Half-open** — after the reset timeout, the next request **probes** the primary again. A **successful** primary call returns to **closed**; a **failure** re-**opens** the breaker.

Logs emit lifecycle hints (`circuit_breaker_opened`, `circuit_breaker_half_open`, `circuit_breaker_closed`).

## Configuration

| Variable | Meaning |
|----------|---------|
| `CIRCUIT_BREAKER_FAIL_MAX` | Failures in closed state before opening |
| `CIRCUIT_BREAKER_RESET_SECONDS` | Seconds to stay open before half-open probe |

## Fallback policy

See [fallback-policy.md](./fallback-policy.md). Optional env flags refine **when** fallback is used for error classes (429, timeout, HTTP 5xx).
