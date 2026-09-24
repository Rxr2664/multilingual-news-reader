import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Source

SOURCES_PATH = Path(__file__).resolve().parents[1] / "data" / "sources.json"


async def seed_sources(session: AsyncSession) -> None:
    data = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    existing = {row[0] for row in (await session.execute(select(Source.feed_url))).all()}
    for item in data:
        if item["feed_url"] in existing:
            continue
        session.add(Source(**item))
