"""Redis utility module for all microservices."""

import json
import asyncio
from typing import Optional, Any
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError


class RedisCache:
    """Redis cache manager with cache-aside pattern."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[dict]:
        """Get value from cache."""
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except (ConnectionError, TimeoutError):
            return None
        except json.JSONDecodeError:
            return None
    
    async def set(self, key: str, value: dict, expire: int = 300) -> bool:
        """Set value in cache with expiration."""
        try:
            data = json.dumps(value, default=str)
            await self.redis.setex(key, expire, data)
            return True
        except (ConnectionError, TimeoutError):
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            await self.redis.delete(key)
            return True
        except (ConnectionError, TimeoutError):
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self.redis.exists(key) == 1
        except (ConnectionError, TimeoutError):
            return False
    
    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return await self.redis.ping()
        except (ConnectionError, TimeoutError):
            return False


async def create_redis_client(host: str = "redis-service", port: int = 6379, 
                              db: int = 0, password: Optional[str] = None) -> Redis:
    """Create Redis client with connection pool."""
    return Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        max_connections=10
    )