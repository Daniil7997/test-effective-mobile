from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.api.v1.routers import main_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = Redis.from_url(settings.url_redis)
    FastAPICache.init(RedisBackend(redis_client))
    yield
    await redis_client.aclose()


application = FastAPI(root_path=settings.api_root_url,
                      lifespan=lifespan)

application.include_router(main_router)
