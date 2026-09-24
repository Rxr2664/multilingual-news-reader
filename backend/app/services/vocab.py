from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import KnownWord, User
from app.redis_client import get_redis
from app.cache import lemmas as lemma_cache
from app.cache import scores as score_cache


async def known_set(db: AsyncSession, user_id: int) -> set[str]:
    rows = await db.execute(select(KnownWord.lemma).where(KnownWord.user_id == user_id))
    return {row[0] for row in rows.all()}


async def mark_known(
    db: AsyncSession,
    user: User,
    lemma: str,
    familiarity: int = 3,
) -> User:
    lemma = lemma.lower().strip()
    existing = await db.execute(
        select(KnownWord).where(KnownWord.user_id == user.id, KnownWord.lemma == lemma)
    )
    row = existing.scalar_one_or_none()
    if row is None:
        db.add(KnownWord(user_id=user.id, lemma=lemma, familiarity=familiarity))
        await db.flush()
    else:
        row.familiarity = familiarity

    r = await get_redis()
    article_ids = await lemma_cache.articles_for_lemma(r, lemma)
    await score_cache.invalidate_for_articles(r, user.id, user.vocab_version, article_ids)
    await db.commit()
    await db.refresh(user)
    return user


async def mark_unknown(db: AsyncSession, user: User, lemma: str) -> None:
    lemma = lemma.lower().strip()
    existing = await db.execute(
        select(KnownWord).where(KnownWord.user_id == user.id, KnownWord.lemma == lemma)
    )
    row = existing.scalar_one_or_none()
    if row is not None:
        await db.delete(row)
    r = await get_redis()
    article_ids = await lemma_cache.articles_for_lemma(r, lemma)
    await score_cache.invalidate_for_articles(r, user.id, user.vocab_version, article_ids)
    await db.commit()


async def bulk_import(
    db: AsyncSession, user: User, lemmas: list[str], familiarity: int = 3
) -> User:
    cleaned = sorted({l.lower().strip() for l in lemmas if l.strip()})
    if not cleaned:
        return user

    if len(cleaned) >= settings.bulk_invalidation_threshold:
        existing = await known_set(db, user.id)
        for lemma in cleaned:
            if lemma not in existing:
                db.add(KnownWord(user_id=user.id, lemma=lemma, familiarity=familiarity))
        user.vocab_version += 1
        await score_cache.bump_vocab_version_metric()
        await db.commit()
        await db.refresh(user)
        return user

    for lemma in cleaned:
        await mark_known(db, user, lemma, familiarity)
    await db.refresh(user)
    return user
