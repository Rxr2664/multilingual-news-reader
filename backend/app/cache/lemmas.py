import json

from redis.asyncio import Redis

from app.config import settings
from app.metrics import lemma_cache_hits, lemma_cache_misses

LEMMA_KEY = "lemmas:{article_id}"
INDEX_KEY = "lemma_index:{lemma}"


async def get_cached_lemmas(r: Redis, article_id: int) -> dict | None:
    raw = await r.get(LEMMA_KEY.format(article_id=article_id))
    if raw:
        lemma_cache_hits.inc()
        return json.loads(raw)
    lemma_cache_misses.inc()
    return None


async def set_cached_lemmas(r: Redis, article_id: int, payload: dict) -> None:
    await r.set(
        LEMMA_KEY.format(article_id=article_id),
        json.dumps(payload),
        ex=settings.lemma_cache_ttl,
    )


async def index_article_lemmas(r: Redis, article_id: int, lemmas: list[str]) -> None:
    pipe = r.pipeline()
    for lemma in set(lemmas):
        pipe.sadd(INDEX_KEY.format(lemma=lemma), article_id)
    await pipe.execute()


async def articles_for_lemma(r: Redis, lemma: str) -> set[int]:
    members = await r.smembers(INDEX_KEY.format(lemma=lemma))
    return {int(m) for m in members}
