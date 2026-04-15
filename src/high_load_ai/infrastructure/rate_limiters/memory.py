from __future__ import annotations

import time

from high_load_ai.domain.ports import RateLimiter


class InMemoryRateLimiter(RateLimiter):
    def __init__(self) -> None:
        self._state: dict[str, tuple[int, float]] = {}

    async def allow(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        count, window_start = self._state.get(key, (0, now))

        if now - window_start >= window_seconds:
            count = 0
            window_start = now

        count += 1
        self._state[key] = (count, window_start)

        remaining = max(limit - count, 0)
        retry_after = max(int(window_seconds - (now - window_start)), 1)

        if count > limit:
            return False, retry_after
        return True, remaining
