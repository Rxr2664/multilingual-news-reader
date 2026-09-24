from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone

import feedparser
import httpx
import trafilatura
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.lemmas import index_article_lemmas, set_cached_lemmas
from app.metrics import nlp_seconds, worker_articles_ingested
from app.models import Article, ArticleLemma, Source
from app.redis_client import get_redis
from app.services.nlp import from_spacy_doc, fallback_tokenize, token_to_dict

log = logging.getLogger("worker.rss")

HEADERS = {"User-Agent": "MultilingualNewsReader/1.0 (+https://localhost)"}

NLP_MODELS: dict[str, object] = {}
LANG_TO_MODEL = {
    "fr": "fr_core_news_sm",
    "es": "es_core_news_sm",
    "de": "de_core_news_sm",
    "it": "it_core_news_sm",
}


def get_nlp(language: str):
    if language in NLP_MODELS:
        return NLP_MODELS[language]
    name = LANG_TO_MODEL.get(language)
    if not name:
        NLP_MODELS[language] = None
        return None
    try:
        import spacy

        NLP_MODELS[language] = spacy.load(name)
    except Exception as exc:  # pragma: no cover - model optional in tests
        log.warning("spaCy model %s unavailable: %s", name, exc)
        NLP_MODELS[language] = None
    return NLP_MODELS[language]


def content_hash(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def lemmatize(text: str, language: str):
    nlp = get_nlp(language)
    started = time.perf_counter()
    if nlp is None:
        processed = fallback_tokenize(text)
    else:
        processed = from_spacy_doc(nlp(text))
    nlp_seconds.observe(time.perf_counter() - started)
    return processed


async def fetch_feed(client: httpx.AsyncClient, url: str):
    res = await client.get(url)
    res.raise_for_status()
    return feedparser.parse(
        res.content,
        response_headers={
            "content-type": res.headers.get("content-type", ""),
            # Base for relative links, as when feedparser fetched the URL itself.
            "content-location": str(res.url),
        },
    )


async def extract_body(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        res = await client.get(url)
        res.raise_for_status()
    except httpx.HTTPError as exc:
        log.info("fetch failed %s: %s", url, exc)
        return None
    return trafilatura.extract(res.text) or None


async def ingest_source(session: AsyncSession, source: Source, max_items: int = 15) -> int:
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=HEADERS) as client:
        return await _ingest_feed(session, client, source, max_items)


async def _ingest_feed(
    session: AsyncSession, client: httpx.AsyncClient, source: Source, max_items: int
) -> int:
    parsed = await fetch_feed(client, source.feed_url)
    ingested = 0
    r = await get_redis()
    for entry in parsed.entries[:max_items]:
        url = entry.get("link")
        if not url:
            continue
        exists = await session.execute(select(Article.id).where(Article.url == url))
        if exists.scalar_one_or_none():
            continue
        body = await extract_body(client, url)
        if not body or len(body) < 400:
            summary = entry.get("summary") or entry.get("description") or ""
            body = trafilatura.extract(summary) or summary
        if not body or len(body) < 80:
            continue
        digest = content_hash(body)
        dup = await session.execute(select(Article.id).where(Article.content_hash == digest))
        if dup.scalar_one_or_none():
            continue
        published = _entry_date(entry)
        processed = lemmatize(body, source.language)
        article = Article(
            source_id=source.id,
            title=(entry.get("title") or "Untitled")[:500],
            body=body,
            url=url[:1000],
            published_at=published,
            content_hash=digest,
            language=source.language,
        )
        session.add(article)
        await session.flush()
        tokens = [token_to_dict(t) for t in processed.tokens]
        session.add(
            ArticleLemma(
                article_id=article.id,
                tokens=tokens,
                lemmas=processed.lemmas,
                content_lemma_count=processed.content_lemma_count,
            )
        )
        await set_cached_lemmas(
            r,
            article.id,
            {
                "tokens": tokens,
                "lemmas": processed.lemmas,
                "content_lemma_count": processed.content_lemma_count,
            },
        )
        await index_article_lemmas(r, article.id, processed.lemmas)
        worker_articles_ingested.labels(language=source.language).inc()
        ingested += 1
    source.last_polled_at = datetime.now(timezone.utc)
    source.last_status = "ok"
    await session.commit()
    return ingested


def _entry_date(entry) -> datetime:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)
