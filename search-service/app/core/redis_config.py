"""Redis configuration for search service."""

import redis.asyncio as redis
from .config import settings


async def get_redis_client() -> redis.Redis:
    """Get Redis client with connection pooling."""
    client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    return client