"""Main comment service application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
from .core.logger import setup_logging
from .core.config import settings
from .core.metrics import setup_metrics
from .core.log_context import LogContextMiddleware
from .api.api import api_router
from .db.session import sync_engine, async_engine
from .db.base import Base
from .core.redis_health import check_redis_health
from .core.event_producer import close_event_producer

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

    await close_event_producer()
    logging.info("Comment service shutting down")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    root_path=settings.ROOT_PATH,
    lifespan=lifespan
)

public_root_path = settings.ROOT_PATH.rstrip("/")
docs_prefix = f"/api{public_root_path}" if public_root_path else ""
public_openapi_url = f"{public_root_path}/openapi.json" if public_root_path else "/openapi.json"


def public_openapi_schema():
    """Return OpenAPI paths as public Kong paths instead of internal /api paths."""
    schema = app.openapi()
    if not public_root_path:
        return schema

    internal_prefix = f"/api{public_root_path}"
    public_schema = dict(schema)
    public_paths = {}

    for path, definition in schema.get("paths", {}).items():
        if path == internal_prefix:
            public_paths[public_root_path] = definition
        elif path.startswith(f"{internal_prefix}/"):
            public_paths[f"{public_root_path}{path[len(internal_prefix):]}"] = definition

    public_schema["paths"] = public_paths
    public_schema["servers"] = [{"url": ""}]
    return public_schema


@app.get(f"{docs_prefix}/openapi.json", include_in_schema=False)
async def openapi_json():
    """OpenAPI schema endpoint behind Kong path rewriting."""
    return JSONResponse(public_openapi_schema())


@app.get(f"{docs_prefix}/docs", include_in_schema=False)
async def swagger_docs():
    """Swagger UI endpoint behind Kong path rewriting."""
    return get_swagger_ui_html(openapi_url=public_openapi_url, title=f"{settings.APP_NAME} - Swagger UI")


@app.get(f"{docs_prefix}/redoc", include_in_schema=False)
async def redoc_docs():
    """ReDoc endpoint behind Kong path rewriting."""
    return get_redoc_html(openapi_url=public_openapi_url, title=f"{settings.APP_NAME} - ReDoc")


# Attach logging context middleware (extracts Kong-Request-ID)
app.add_middleware(LogContextMiddleware)

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
