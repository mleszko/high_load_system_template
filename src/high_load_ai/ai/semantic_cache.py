from __future__ import annotations

import hashlib
import json
import logging
import math
import struct

from redis.asyncio import Redis

from high_load_ai.core.config import Settings

logger = logging.getLogger(__name__)


def _pseudo_embedding(text: str, dimensions: int) -> list[float]:
    """Deterministic pseudo-embedding for tests and air-gapped mode."""
    vec: list[float] = []
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    for i in range(dimensions):
        b = seed[i % len(seed)]
        vec.append((b - 127.5) / 127.5)
    return vec


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _bucket_id(vec: list[float], bits: int) -> int:
    h = hashlib.sha256()
    for x in vec[: min(64, len(vec))]:
        h.update(struct.pack("f", float(x)))
    digest: int = int(h.hexdigest()[:12], 16)
    modulus = int(2**bits)
    return digest % modulus


class SemanticLlmCache:
    """
    Redis-backed semantic cache: vectors grouped into buckets to cap scan cost.

    At very large scale, replace with RediSearch or an external vector index.
    """

    max_entries_per_bucket = 200

    def __init__(self, redis: Redis, settings: Settings) -> None:
        self._redis = redis
        self._settings = settings

    def enabled(self) -> bool:
        return self._settings.semantic_cache_enabled and not self._settings.llm_stub_enabled

    def _bucket_key(self, vec: list[float]) -> str:
        b = _bucket_id(vec, self._settings.semantic_cache_bucket_bits)
        return f"sem:llm:bkt:{b}"

    async def _embed(self, prompt: str) -> list[float]:
        if self._settings.semantic_cache_embed_mode == "openai":
            from langchain_openai import OpenAIEmbeddings
            from pydantic import SecretStr

            embedder = OpenAIEmbeddings(
                model=self._settings.semantic_cache_embed_model,
                api_key=SecretStr(self._settings.llm_api_key),
                base_url=self._settings.llm_base_url,
            )
            vec = await embedder.aembed_query(prompt)
            return list(vec)

        return _pseudo_embedding(prompt, self._settings.semantic_cache_hash_dimensions)

    async def lookup(self, prompt: str) -> str | None:
        if not self.enabled():
            return None

        vec = await self._embed(prompt)
        bkey = self._bucket_key(vec)
        raw_items = await self._redis.lrange(bkey, 0, self.max_entries_per_bucket - 1)  # type: ignore[misc]
        best_text: str | None = None
        best_score = self._settings.semantic_cache_min_similarity

        for raw in raw_items:
            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                continue
            candidate_vec = item.get("vec")
            text = item.get("text")
            if not isinstance(candidate_vec, list) or not isinstance(text, str):
                continue
            score = _cosine(vec, [float(x) for x in candidate_vec])
            if score >= best_score:
                best_score = score
                best_text = text

        if best_text is not None:
            logger.info("semantic_cache_hit bucket=%s similarity=%.4f", bkey, best_score)
        return best_text

    async def store(self, prompt: str, text: str) -> None:
        if not self.enabled() or not text.strip():
            return

        vec = await self._embed(prompt)
        bkey = self._bucket_key(vec)
        payload = json.dumps({"vec": vec, "text": text})
        await self._redis.lpush(bkey, payload)  # type: ignore[misc]
        await self._redis.ltrim(bkey, 0, self.max_entries_per_bucket - 1)  # type: ignore[misc]
