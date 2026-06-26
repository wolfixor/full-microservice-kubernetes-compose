"""Redis health check for search service."""

import logging
from .redis_config import get_redis_client


async def check_redis_health() -> dict:
    """Check Redis connection health."""
    logger = logging.getLogger(__name__)
    
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        
        # Test basic operations
        await redis_client.set("health_check", "ok", ex=5)
        value = await redis_client.get("health_check")
        
        if value == "ok":
            return {"connected": True, "message": "Redis is healthy"}
        else:
            return {"connected": False, "message": "Redis read/write test failed"}
            
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return {"connected": False, "message": str(e)}
    finally:
        try:
            redis_client = await get_redis_client()
            await redis_client.close()
        except:
            pass