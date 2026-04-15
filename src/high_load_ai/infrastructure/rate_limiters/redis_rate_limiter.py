from __future__ import annotations

from redis.asyncio import Redis

from high_load_ai.domain.ports import RateLimiter


class RedisRateLimiter(RateLimiter):
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def allow(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        bucket_key = f"ratelimit:{key}"
        count = await self._client.incr(bucket_key)
        if count == 1:
            await self._client.expire(bucket_key, window_seconds)
        ttl = await self._client.ttl(bucket_key)
        remaining = max(limit - int(count), 0)
        if count > limit:
            return False, max(ttl, 1)
        return True, remaining
