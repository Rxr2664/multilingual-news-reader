from redis.asyncio import Redis

from app.config import settings

redis: Redis | None = None


async def get_redis() -> Redis:
    global redis
    if redis is None:
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return redis


async def close_redis() -> None:
    global redis
    if redis is not None:
        await redis.aclose()
        redis = None
