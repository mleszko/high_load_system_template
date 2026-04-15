# Semantic LLM cache

## Purpose

**Semantically similar** prompts can reuse a previous completion **without** calling the LLM, reducing cost and latency.

## Modes

| Mode | Env | Use case |
|------|-----|----------|
| **Hash** | `SEMANTIC_CACHE_EMBED_MODE=hash` | Tests, air-gapped dev; deterministic pseudo-embeddings |
| **OpenAI-compatible** | `SEMANTIC_CACHE_EMBED_MODE=openai` | Production; uses `LLM_BASE_URL` + `LLM_API_KEY` and `SEMANTIC_CACHE_EMBED_MODEL` |

## Bucketing (scale)

Entries are sharded by a **bucket** derived from the embedding vector so lookup scans only a small Redis list (`sem:llm:bkt:{bucket}`) instead of one global list.

Tune with `SEMANTIC_CACHE_BUCKET_BITS` (more bits → more buckets, smaller lists per bucket).

## Similarity

- `SEMANTIC_CACHE_MIN_SIMILARITY` — cosine similarity threshold (0–1). Raise to reduce false positives; lower to increase hit rate.

## Events

SSE may include `semantic_cache:hit` / `semantic_cache:miss` and a `cached` event with the reused text.

## Configuration summary

- `SEMANTIC_CACHE_ENABLED`
- `SEMANTIC_CACHE_EMBED_MODE`
- `SEMANTIC_CACHE_EMBED_MODEL`
- `SEMANTIC_CACHE_MIN_SIMILARITY`
- `SEMANTIC_CACHE_HASH_DIM`
- `SEMANTIC_CACHE_BUCKET_BITS`

For very large catalogs, replace bucket lists with **RediSearch** or an external vector database (same port boundaries).
