import asyncio
import logging
import os
import sys
from pathlib import Path

from prometheus_client import start_http_server
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.db import SessionLocal, engine, Base
from app.models import Source
from app.seed import seed_sources
from worker.rss import ingest_source

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("worker")


async def poll_once() -> None:
    async with SessionLocal() as session:
        sources = (await session.execute(select(Source))).scalars().all()
        for source in sources:
            try:
                n = await ingest_source(session, source)
                log.info("ingested %s from %s", n, source.name)
            except Exception:
                log.exception("failed ingesting %s", source.name)
                await session.rollback()
                source.last_status = "error"
                session.add(source)
                await session.commit()


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_sources(session)
        await session.commit()

    # The worker is its own process, so it serves its own /metrics for Prometheus.
    if settings.worker_metrics_port:
        start_http_server(settings.worker_metrics_port)
        log.info("metrics on :%s", settings.worker_metrics_port)

    interval = int(os.getenv("WORKER_POLL_SECONDS", settings.worker_poll_seconds))
    while True:
        log.info("poll start")
        await poll_once()
        log.info("sleeping %ss", interval)
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())
