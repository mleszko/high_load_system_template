from __future__ import annotations

import httpx

from high_load_ai.ai.fallback_policy import FallbackPolicy, should_fallback


def test_fallback_on_429_respects_policy() -> None:
    policy = FallbackPolicy(on_429=False)
    exc = httpx.HTTPStatusError(
        "rate limit",
        request=httpx.Request("GET", "http://test"),
        response=httpx.Response(429, request=httpx.Request("GET", "http://test")),
    )
    assert should_fallback(exc, policy) is False

    policy_on = FallbackPolicy(on_429=True)
    assert should_fallback(exc, policy_on) is True
