import httpx
import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app.cache.lemmas import articles_for_lemma, get_cached_lemmas
from app.models import Article, ArticleLemma, Source
from app.redis_client import get_redis
from worker import rss

FEED_URL = "https://news.example.com/rss.xml"
ARTICLE_URL = "https://news.example.com/2026/09/pluie"

SUMMARY = (
    "La pluie continue de tomber sur la région et les habitants surveillent "
    "le niveau des rivières."
)
PARAGRAPHS = [
    "Depuis le début de la semaine, la pluie tombe sans arrêt sur la région et les "
    "rivières montent lentement. Les habitants des villages proches du fleuve "
    "surveillent le niveau de l'eau chaque matin, tandis que la mairie a ouvert une "
    "salle pour accueillir les familles qui préfèrent quitter leur maison pendant "
    "quelques jours.",
    "Les services météo annoncent encore trois jours de pluie avant une amélioration "
    "attendue dimanche. En attendant, les écoles restent ouvertes, mais plusieurs "
    "routes secondaires sont fermées et les agriculteurs craignent pour les récoltes "
    "de fin de saison.",
]
ARTICLE_HTML = (
    "<html><head><title>La pluie continue</title></head><body><article>"
    "<h1>La pluie continue</h1>"
    + "".join(f"<p>{p}</p>" for p in PARAGRAPHS)
    + "</article></body></html>"
)


def feed_xml(*links: str) -> bytes:
    items = "".join(
        f"""
    <item>
      <title>La pluie continue</title>
      <link>{link}</link>
      <description>{SUMMARY}</description>
      <pubDate>Wed, 23 Sep 2026 08:00:00 GMT</pubDate>
    </item>"""
        for link in links
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Exemple</title>
    <link>https://news.example.com/</link>
    <description>Flux de test</description>{items}
  </channel>
</rss>""".encode("utf-8")


def mock_feed(respx_mock, *links: str):
    return respx_mock.get(FEED_URL).mock(
        return_value=httpx.Response(
            200,
            content=feed_xml(*links),
            headers={"content-type": "application/rss+xml; charset=utf-8"},
        )
    )


def mock_page(respx_mock, url: str):
    return respx_mock.get(url).mock(return_value=httpx.Response(200, html=ARTICLE_HTML))


@pytest_asyncio.fixture
async def source(db) -> Source:
    src = Source(name="Exemple", feed_url=FEED_URL, country="FR", language="fr")
    db.add(src)
    await db.commit()
    await db.refresh(src)
    return src


@pytest.mark.asyncio
async def test_ingest_stores_article_and_fills_caches(db, source, respx_mock):
    mock_feed(respx_mock, ARTICLE_URL)
    mock_page(respx_mock, ARTICLE_URL)

    assert await rss.ingest_source(db, source) == 1

    article = (await db.execute(select(Article))).scalar_one()
    assert article.url == ARTICLE_URL
    assert article.title == "La pluie continue"
    lemma_row = await db.get(ArticleLemma, article.id)
    assert "pluie" in lemma_row.lemmas
    assert source.last_status == "ok"

    r = await get_redis()
    assert article.id in await articles_for_lemma(r, "pluie")
    cached = await get_cached_lemmas(r, article.id)
    assert cached["lemmas"] == lemma_row.lemmas


@pytest.mark.asyncio
async def test_second_poll_skips_known_urls(db, source, respx_mock):
    feed = mock_feed(respx_mock, ARTICLE_URL)
    page = mock_page(respx_mock, ARTICLE_URL)

    assert await rss.ingest_source(db, source) == 1
    assert await rss.ingest_source(db, source) == 0
    assert feed.call_count == 2
    assert page.call_count == 1


@pytest.mark.asyncio
async def test_same_story_at_two_urls_is_stored_once(db, source, respx_mock):
    other_url = "https://news.example.com/2026/09/pluie-bis"
    mock_feed(respx_mock, ARTICLE_URL, other_url)
    mock_page(respx_mock, ARTICLE_URL)
    mock_page(respx_mock, other_url)

    assert await rss.ingest_source(db, source) == 1
    count = (await db.execute(select(func.count()).select_from(Article))).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_feed_is_fetched_with_worker_user_agent(db, source, respx_mock):
    feed = mock_feed(respx_mock)

    assert await rss.ingest_source(db, source) == 0
    user_agent = feed.calls.last.request.headers["user-agent"]
    assert user_agent.startswith("MultilingualNewsReader/")


@pytest.mark.asyncio
async def test_feed_http_error_propagates(db, source, respx_mock):
    respx_mock.get(FEED_URL).mock(return_value=httpx.Response(503))

    with pytest.raises(httpx.HTTPStatusError):
        await rss.ingest_source(db, source)
