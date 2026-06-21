"""Redis health check utility."""

import logging
from typing import Dict, Any
from .redis_config import redis_settings
from .redis_utils import create_redis_client


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connection health."""
    try:
        redis_client = await create_redis_client(
            host=redis_settings.REDIS_HOST,
            port=redis_settings.REDIS_PORT,
            db=redis_settings.REDIS_DB,
            password=redis_settings.REDIS_PASSWORD
        )
        
        # Test connection
        is_alive = await redis_client.ping()
        
        # Get Redis info
        info = await redis_client.info()
        
        await redis_client.close()
        
        return {
            "status": "healthy" if is_alive else "unhealthy",
            "connected": is_alive,
            "version": info.get("redis_version", "unknown"),
            "memory_used": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "role": info.get("role", "unknown"),
            "db_size": info.get(f"db{redis_settings.REDIS_DB}", {}).get("keys", 0)
        }
    except Exception as e:
        logging.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }