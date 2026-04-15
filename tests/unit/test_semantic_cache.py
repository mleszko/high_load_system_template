from __future__ import annotations

import fakeredis.aioredis
import pytest

from high_load_ai.ai.semantic_cache import SemanticLlmCache
from high_load_ai.core.config import Settings


@pytest.mark.asyncio
async def test_semantic_cache_hit_similar_prompts() -> None:
    settings = Settings(
        app_env="dev",
        semantic_cache_enabled=True,
        semantic_cache_embed_mode="hash",
        semantic_cache_min_similarity=0.99,
        semantic_cache_hash_dimensions=32,
        llm_stub=False,
    )
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    cache = SemanticLlmCache(redis, settings)

    await cache.store("hello world", "cached answer")
    hit = await cache.lookup("hello world")
    assert hit == "cached answer"
