from redis.asyncio import Redis

from app.config import settings
from app.metrics import score_cache_hits, score_cache_misses, score_invalidations

SCORE_KEY = "score:{user_id}:{vocab_version}:{article_id}"


def score_key(user_id: int, vocab_version: int, article_id: int) -> str:
    return SCORE_KEY.format(
        user_id=user_id, vocab_version=vocab_version, article_id=article_id
    )


async def get_score(
    r: Redis, user_id: int, vocab_version: int, article_id: int
) -> float | None:
    raw = await r.get(score_key(user_id, vocab_version, article_id))
    if raw is not None:
        score_cache_hits.inc()
        return float(raw)
    score_cache_misses.inc()
    return None


async def set_score(
    r: Redis, user_id: int, vocab_version: int, article_id: int, pct: float
) -> None:
    await r.set(
        score_key(user_id, vocab_version, article_id),
        str(pct),
        ex=settings.score_cache_ttl,
    )


async def invalidate_for_articles(
    r: Redis, user_id: int, vocab_version: int, article_ids: set[int]
) -> int:
    """Precise invalidation used for a single-word learn."""
    if not article_ids:
        return 0
    keys = [score_key(user_id, vocab_version, aid) for aid in article_ids]
    deleted = 0
    # Unlink in chunks so a large but still-targeted delete stays non-blocking.
    chunk = 500
    for i in range(0, len(keys), chunk):
        deleted += await r.unlink(*keys[i : i + chunk])
    score_invalidations.labels(strategy="reverse_index").inc(deleted)
    return deleted


async def bump_vocab_version_metric() -> None:
    score_invalidations.labels(strategy="version_bump").inc()
