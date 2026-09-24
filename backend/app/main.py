from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.config import settings
from app.db import Base, engine, SessionLocal
from app.models import Source  # noqa: F401
from app.redis_client import close_redis
from app.routers import articles, auth, health, onboarding, vocab
from app.seed import seed_sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_articles_source_published_desc "
                "ON articles (source_id, published_at DESC)"
            )
        )
    async with SessionLocal() as session:
        await seed_sources(session)
        await session.commit()
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(title="Multilingual News Reader", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(articles.router)
app.include_router(vocab.router)
app.include_router(onboarding.router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
