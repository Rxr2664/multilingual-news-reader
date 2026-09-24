from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import create_access_token
from app.config import settings
from app.db import Base, get_db
from app.main import app
from app.models import Article, ArticleLemma, KnownWord, Source, User
from app.redis_client import close_redis, get_redis

TEST_DB = settings.database_url


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db, db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def override_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await close_redis()


@pytest_asyncio.fixture
async def user(db: AsyncSession) -> User:
    u = User(email="test@example.com", name="Test", target_language="fr", target_country="FR")
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest_asyncio.fixture
def token(user: User) -> str:
    return create_access_token(user.id, user.email)


@pytest_asyncio.fixture
async def article(db: AsyncSession) -> Article:
    source = Source(
        name="Le Monde",
        feed_url="https://example.com/rss",
        country="FR",
        language="fr",
    )
    db.add(source)
    await db.flush()
    art = Article(
        source_id=source.id,
        title="Malgré la pluie, Paris avance",
        body="Malgré la pluie, Paris avance et le gouvernement parle.",
        url="https://example.com/a1",
        published_at=datetime.now(timezone.utc),
        content_hash="abc123",
        language="fr",
    )
    db.add(art)
    await db.flush()
    lemmas = ["malgré", "pluie", "avancer", "gouvernement", "parler"]
    tokens = [
        {"text": "Malgré", "lemma": "malgré", "is_entity": False, "is_punct": False},
        {"text": " ", "lemma": " ", "is_entity": False, "is_punct": True},
        {"text": "la", "lemma": "le", "is_entity": False, "is_punct": False},
        {"text": " ", "lemma": " ", "is_entity": False, "is_punct": True},
        {"text": "pluie", "lemma": "pluie", "is_entity": False, "is_punct": False},
        {"text": ",", "lemma": ",", "is_entity": False, "is_punct": True},
        {"text": " ", "lemma": " ", "is_entity": False, "is_punct": True},
        {"text": "Paris", "lemma": "Paris", "is_entity": True, "is_punct": False},
        {"text": " ", "lemma": " ", "is_entity": False, "is_punct": True},
        {"text": "avance", "lemma": "avancer", "is_entity": False, "is_punct": False},
        {"text": ".", "lemma": ".", "is_entity": False, "is_punct": True},
    ]
    db.add(
        ArticleLemma(
            article_id=art.id,
            tokens=tokens,
            lemmas=lemmas,
            content_lemma_count=len(lemmas),
        )
    )
    await db.commit()
    await db.refresh(art)
    r = await get_redis()
    from app.cache.lemmas import index_article_lemmas, set_cached_lemmas

    await index_article_lemmas(r, art.id, lemmas)
    await set_cached_lemmas(
        r,
        art.id,
        {"tokens": tokens, "lemmas": lemmas, "content_lemma_count": len(lemmas)},
    )
    return art
