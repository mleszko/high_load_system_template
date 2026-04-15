from __future__ import annotations

import json
from typing import Any, cast

from redis.asyncio import Redis


class ExactRunCache:
    """Short-TTL exact cache for idempotent read models (e.g. GET run by id)."""

    def __init__(self, redis: Redis, *, key_prefix: str = "cache:run:", ttl_seconds: int = 30) -> None:
        self._redis = redis
        self._prefix = key_prefix
        self._ttl = ttl_seconds

    def _key(self, run_id: str) -> str:
        return f"{self._prefix}{run_id}"

    async def get(self, run_id: str) -> dict[str, Any] | None:
        raw = await self._redis.get(self._key(run_id))
        if raw is None:
            return None
        return cast(dict[str, Any], json.loads(raw))

    async def set(self, run_id: str, payload: dict[str, Any]) -> None:
        await self._redis.set(self._key(run_id), json.dumps(payload), ex=self._ttl)

    async def delete(self, run_id: str) -> None:
        await self._redis.delete(self._key(run_id))
