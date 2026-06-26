"""Main comment service application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .core.logger import setup_logging
from .core.config import settings
from .core.metrics import setup_metrics
from .api.api import api_router
from .db.session import sync_engine, async_engine
from .db.base import Base
from .core.redis_health import check_redis_health

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Test database connection only
    # Migrations are handled by docker-entrypoint.sh
    try:
        from sqlalchemy import text
        from .db.session import async_engine
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logging.info("Database connection verified")
    except Exception as e:
        logging.warning(f"Database connection failed: {e}")

    yield

    # Shutdown: Nothing special for now
    logging.info("Comment service shutting down")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=settings.ROOT_PATH,
    lifespan=lifespan
)

# Include API router
app.include_router(api_router, prefix="/api")

# Setup Prometheus metrics
setup_metrics(app, async_engine)


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

    logger.info(f"Comment service readiness check: Redis {'healthy' if is_ready else 'unhealthy'}")

    return {
        "status": "ready" if is_ready else "not_ready",
        "service": settings.APP_NAME,
        "redis": redis_health
    }