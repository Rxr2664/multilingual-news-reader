import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_demo_login(client: AsyncClient):
    res = await client.post("/auth/demo", params={"email": "a@b.com"})
    assert res.status_code == 200
    assert "access_token" in res.json()
