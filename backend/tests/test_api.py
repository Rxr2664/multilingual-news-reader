import pytest
from httpx import AsyncClient

from app.models import User


@pytest.mark.asyncio
async def test_demo_login(client: AsyncClient):
    res = await client.post("/auth/demo", params={"email": "a@b.com"})
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_article_list_requires_auth(client: AsyncClient):
    res = await client.get("/articles")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_article_list_and_know_word(client: AsyncClient, token: str, article, user: User):
    headers = {"Authorization": f"Bearer {token}"}
    listed = await client.get("/articles?country=FR&language=fr", headers=headers)
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    before = body[0]["unknown_pct"]
    detail = await client.get(f"/articles/{article.id}", headers=headers)
    assert detail.status_code == 200
    tokens = detail.json()["tokens"]
    assert any(t["unknown"] for t in tokens if t["lemma"] == "malgré")
    known = await client.post("/vocab/know", json={"lemma": "malgré"}, headers=headers)
    assert known.status_code == 200
    listed2 = await client.get("/articles?country=FR&language=fr", headers=headers)
    after = listed2.json()[0]["unknown_pct"]
    assert after < before
