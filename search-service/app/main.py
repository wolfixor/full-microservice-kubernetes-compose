"""Main search service application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .core.logger import setup_logging
from .core.config import settings
from .api.api import api_router
from .repositories.search_repository import SearchRepository
from .core.redis_health import check_redis_health
from .core.elasticsearch_config import close_elasticsearch_client

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Initialize Elasticsearch index
    logger = logging.getLogger(__name__)
    try:
        repository = SearchRepository()
        await repository.initialize_index()
        logger.info("Elasticsearch index initialized")
    except Exception as e:
        logger.warning(f"Elasticsearch initialization failed: {e}")
    
    yield
    
    # Shutdown: Close connections
    logger.info("Search service shutting down")
    await close_elasticsearch_client()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    root_path="/search",
    lifespan=lifespan
)

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint with Redis health check."""
    logger = logging.getLogger(__name__)
    
    # Check Redis health
    redis_health = await check_redis_health()
    
    # Determine overall readiness
    is_ready = redis_health.get("connected", False)
    
    logger.info(f"Search service readiness check: Redis {'healthy' if is_ready else 'unhealthy'}")
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "service": settings.APP_NAME,
        "redis": redis_health
    }