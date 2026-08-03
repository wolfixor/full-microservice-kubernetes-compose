"""Redis configuration for search service."""

import redis.asyncio as redis
from redis.asyncio.cluster import RedisCluster
from .config import settings


async def get_redis_client() -> redis.Redis:
    """Get Redis client with connection pooling."""
    if settings.REDIS_CLUSTER_ENABLED:
        connection_kwargs = {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "require_full_coverage": False,
        }

        if settings.REDIS_PASSWORD:
            connection_kwargs["password"] = settings.REDIS_PASSWORD

        return RedisCluster(**connection_kwargs)

    client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    return client
