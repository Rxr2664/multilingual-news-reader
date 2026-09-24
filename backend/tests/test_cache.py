import pytest

from app.cache import lemmas as lemma_cache
from app.cache import scores as score_cache
from app.models import User
from app.redis_client import get_redis
from app.services import vocab as vocab_svc


@pytest.mark.asyncio
async def test_single_word_invalidates_reverse_index(db, user: User, article):
    r = await get_redis()
    await lemma_cache.index_article_lemmas(r, article.id, ["malgré", "pluie"])
    await score_cache.set_score(r, user.id, user.vocab_version, article.id, 80.0)
    await vocab_svc.mark_known(db, user, "malgré")
    cached = await score_cache.get_score(r, user.id, user.vocab_version, article.id)
    # get_score increments miss counter; after unlink the key must be gone
    raw = await r.get(score_cache.score_key(user.id, user.vocab_version, article.id))
    assert raw is None
    assert cached is None


@pytest.mark.asyncio
async def test_bulk_import_bumps_vocab_version(db, user: User):
    lemmas = [f"mot{i}" for i in range(60)]
    updated = await vocab_svc.bulk_import(db, user, lemmas)
    assert updated.vocab_version == user.vocab_version or updated.vocab_version >= 2
    assert updated.vocab_version >= 2
