from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class FallbackPolicy:
    on_timeout: bool = True
    on_429: bool = True
    on_5xx: bool = True
    on_other: bool = True


def should_fallback(exc: BaseException, policy: FallbackPolicy) -> bool:
    if isinstance(exc, TimeoutError):
        return policy.on_timeout
    if isinstance(exc, httpx.TimeoutException):
        return policy.on_timeout
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 429:
            return policy.on_429
        if 500 <= code < 600:
            return policy.on_5xx
        return policy.on_other
    status = getattr(exc, "status_code", None)
    if status == 429:
        return policy.on_429
    if isinstance(status, int) and 500 <= status < 600:
        return policy.on_5xx
    return policy.on_other
