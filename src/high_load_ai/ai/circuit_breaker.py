from __future__ import annotations

import logging
import time
from enum import StrEnum

logger = logging.getLogger(__name__)


class BreakerPhase(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerState:
    """Three-phase circuit breaker: closed → open → half-open → closed."""

    def __init__(
        self,
        *,
        fail_max: int = 5,
        reset_timeout_seconds: float = 30.0,
    ) -> None:
        self._fail_max = fail_max
        self._reset_timeout = reset_timeout_seconds
        self._phase = BreakerPhase.CLOSED
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def phase(self) -> BreakerPhase:
        return self._phase

    def allow_primary(self) -> bool:
        if self._phase == BreakerPhase.CLOSED:
            return True
        if self._phase == BreakerPhase.HALF_OPEN:
            return True
        if self._phase == BreakerPhase.OPEN:
            if self._opened_at is None:
                return True
            if time.monotonic() - self._opened_at >= self._reset_timeout:
                self._phase = BreakerPhase.HALF_OPEN
                logger.info("circuit_breaker_half_open")
                return True
            return False
        return True

    def record_primary_success(self) -> None:
        if self._phase == BreakerPhase.HALF_OPEN:
            logger.info("circuit_breaker_closed")
            self._phase = BreakerPhase.CLOSED
            self._failures = 0
            self._opened_at = None
        elif self._phase == BreakerPhase.CLOSED:
            self._failures = 0

    def record_primary_failure(self) -> None:
        if self._phase == BreakerPhase.HALF_OPEN:
            logger.warning("circuit_breaker_opened reason=half_open_probe_failed")
            self._phase = BreakerPhase.OPEN
            self._opened_at = time.monotonic()
            return

        if self._phase == BreakerPhase.CLOSED:
            self._failures += 1
            if self._failures >= self._fail_max:
                logger.warning("circuit_breaker_opened reason=fail_threshold failures=%s", self._failures)
                self._phase = BreakerPhase.OPEN
                self._opened_at = time.monotonic()
