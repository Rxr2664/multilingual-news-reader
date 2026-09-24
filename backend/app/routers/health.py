from fastapi import APIRouter

from app.metrics import lemma_cache_hits, lemma_cache_misses, score_cache_hits, score_cache_misses
from app.schemas import CacheStats

router = APIRouter(tags=["health"])


def _val(counter) -> int:
    return int(counter._value.get())


@router.get("/health")
async def health():
    return {"ok": True}


@router.get("/metrics/cache", response_model=CacheStats)
async def cache_stats():
    lh, lm = _val(lemma_cache_hits), _val(lemma_cache_misses)
    sh, sm = _val(score_cache_hits), _val(score_cache_misses)
    total = lh + lm + sh + sm
    hit_rate = (lh + sh) / total if total else 0.0
    return CacheStats(
        lemma_hits=lh,
        lemma_misses=lm,
        score_hits=sh,
        score_misses=sm,
        hit_rate=round(hit_rate, 4),
    )
