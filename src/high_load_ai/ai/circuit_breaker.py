from __future__ import annotations

import time


class CircuitBreakerState:
    """Minimal circuit breaker (closed / open / half-open) for dependency calls."""

    def __init__(
        self,
        *,
        fail_max: int = 5,
        reset_timeout_seconds: float = 30.0,
    ) -> None:
        self._fail_max = fail_max
        self._reset_timeout = reset_timeout_seconds
        self._failures = 0
        self._opened_at: float | None = None

    def allow(self) -> bool:
        if self._opened_at is None:
            return True
        if time.monotonic() - self._opened_at >= self._reset_timeout:
            return True
        return False

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._fail_max:
            self._opened_at = time.monotonic()

    @property
    def is_open(self) -> bool:
        return not self.allow()
