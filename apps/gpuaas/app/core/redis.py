from functools import lru_cache

from redis.asyncio import Redis

from apps.gpuaas.app.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()

    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=None,
        health_check_interval=30,
        retry_on_timeout=True,
    )
