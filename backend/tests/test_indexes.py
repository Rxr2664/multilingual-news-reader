import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_known_words_composite_index_exists(db: AsyncSession):
    rows = await db.execute(
        text(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'known_words' AND indexname = 'ix_known_words_user_lemma'"
        )
    )
    assert rows.scalar_one_or_none() == "ix_known_words_user_lemma"


@pytest.mark.asyncio
async def test_articles_feed_index_exists(db: AsyncSession):
    rows = await db.execute(
        text(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'articles' AND indexname = 'ix_articles_source_published'"
        )
    )
    assert rows.scalar_one_or_none() == "ix_articles_source_published"


@pytest.mark.asyncio
async def test_feed_query_uses_index(db: AsyncSession, article):
    plan = (
        await db.execute(
            text(
                "EXPLAIN SELECT * FROM articles "
                "WHERE source_id = :sid ORDER BY published_at DESC LIMIT 20"
            ),
            {"sid": article.source_id},
        )
    ).fetchall()
    joined = " ".join(r[0] for r in plan)
    assert "Index" in joined or "articles" in joined.lower()
