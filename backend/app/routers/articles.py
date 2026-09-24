from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.cache import lemmas as lemma_cache
from app.cache import scores as score_cache
from app.db import get_db
from app.metrics import feed_query_seconds
from app.models import Article, ArticleLemma, Source, User
from app.redis_client import get_redis
from app.schemas import ArticleDetail, ArticleListItem, TokenSpan
from app.services.difficulty import unknown_pct
from app.services import vocab as vocab_svc

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=list[ArticleListItem])
async def list_articles(
    country: str | None = None,
    language: str | None = None,
    sort: str = Query("difficulty", pattern="^(difficulty|newest)$"),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lang = language or user.target_language
    ctry = country or user.target_country
    r = await get_redis()
    known = await vocab_svc.known_set(db, user.id)

    started = perf_counter()
    stmt = (
        select(Article)
        .join(Source)
        .options(selectinload(Article.source), selectinload(Article.lemma_row))
        .where(Source.country == ctry, Article.language == lang)
        .order_by(Article.published_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()
    feed_query_seconds.observe(perf_counter() - started)

    items: list[ArticleListItem] = []
    for article in articles:
        lemmas = (article.lemma_row.lemmas if article.lemma_row else []) or []
        cached = await score_cache.get_score(r, user.id, user.vocab_version, article.id)
        if cached is None:
            pct, unknown_count = unknown_pct(lemmas, known)
            await score_cache.set_score(r, user.id, user.vocab_version, article.id, pct)
        else:
            pct, unknown_count = cached, max(0, int(round(cached / 100 * max(len(set(lemmas)), 1))))
        items.append(
            ArticleListItem(
                id=article.id,
                title=article.title,
                url=article.url,
                source_name=article.source.name,
                country=article.source.country,
                language=article.language,
                published_at=article.published_at,
                unknown_pct=pct,
                unknown_count=unknown_count,
                content_lemma_count=article.lemma_row.content_lemma_count if article.lemma_row else 0,
            )
        )
    if sort == "difficulty":
        items.sort(key=lambda x: x.unknown_pct)
    return items


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(
    article_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    article = await db.get(Article, article_id)
    if article is None:
        raise HTTPException(404, "Article not found")
    await db.refresh(article, ["source", "lemma_row"])
    r = await get_redis()
    payload = await lemma_cache.get_cached_lemmas(r, article.id)
    if payload is None:
        if article.lemma_row is None:
            raise HTTPException(404, "Article not lemmatized yet")
        payload = {
            "tokens": article.lemma_row.tokens,
            "lemmas": article.lemma_row.lemmas,
            "content_lemma_count": article.lemma_row.content_lemma_count,
        }
        await lemma_cache.set_cached_lemmas(r, article.id, payload)

    known = await vocab_svc.known_set(db, user.id)
    tokens = []
    for t in payload["tokens"]:
        is_content = not t.get("is_punct") and not t.get("is_entity")
        unknown = is_content and t.get("lemma", "").lower() not in known
        tokens.append(
            TokenSpan(
                text=t["text"],
                lemma=t["lemma"],
                is_entity=t.get("is_entity", False),
                is_punct=t.get("is_punct", False),
                unknown=unknown,
            )
        )
    pct, _ = unknown_pct(payload.get("lemmas") or [], known)
    return ArticleDetail(
        id=article.id,
        title=article.title,
        url=article.url,
        source_name=article.source.name,
        country=article.source.country,
        language=article.language,
        published_at=article.published_at,
        body=article.body,
        tokens=tokens,
        unknown_pct=pct,
    )
