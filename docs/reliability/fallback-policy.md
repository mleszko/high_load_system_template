# LLM fallback policy

When the **primary** model raises an error or the breaker is **open**, the service uses the **fallback** model (`LLM_FALLBACK_MODEL`), typically smaller or faster.

## Environment flags

| Variable | Default | Effect |
|----------|---------|--------|
| `LLM_FALLBACK_ON_TIMEOUT` | `true` | Fallback on timeout-like errors |
| `LLM_FALLBACK_ON_429` | `true` | Fallback on HTTP 429 from provider |
| `LLM_FALLBACK_ON_5XX` | `true` | Fallback on HTTP 5xx |
| `LLM_FALLBACK_ON_OTHER` | `true` | Fallback on other exceptions after primary attempt |

If a flag is `false`, that error class **re-raises** (no silent fallback) when the primary fails.

**Note:** When the breaker is **open** (before half-open), fallback is always used regardless of these flags, so the API remains available.

## Timeouts

- Primary: `LLM_TIMEOUT_SECONDS`
- Fallback: `LLM_FALLBACK_TIMEOUT_SECONDS`
