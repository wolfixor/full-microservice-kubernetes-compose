"""Main search service application."""

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
from .repositories.search_repository import SearchRepository
from .core.redis_health import check_redis_health
from .core.elasticsearch_config import close_elasticsearch_client
from .core.kafka_event_consumer import get_kafka_consumer_health, start_kafka_event_consumer, stop_kafka_event_consumer
from .core.metrics import SERVICE_NAME, redis_health_gauge

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Initialize Elasticsearch index
    logger = logging.getLogger(__name__)
    kafka_consumer = None
    try:
        repository = SearchRepository()
        await repository.initialize_index()
        logger.info("Elasticsearch index initialized")
    except Exception as e:
        logger.warning(f"Elasticsearch initialization failed: {e}")

    try:
        kafka_consumer = start_kafka_event_consumer()
        logger.info("Kafka event consumer scheduled")
    except Exception as e:
        logger.warning(f"Kafka consumer startup failed: {e}")

    yield

    # Shutdown: Close connections
    logger.info("Search service shutting down")
    if kafka_consumer:
        await stop_kafka_event_consumer(*kafka_consumer)
    await close_elasticsearch_client()


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
setup_metrics(app)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint with dependency health checks."""
    logger = logging.getLogger(__name__)

    redis_health = await check_redis_health()
    kafka_health = get_kafka_consumer_health()

    redis_ready = redis_health.get("connected", False)
    kafka_ready = kafka_health.get("active", False)
    is_ready = redis_ready and kafka_ready

    redis_health_gauge.labels(service=SERVICE_NAME).set(1 if redis_ready else 0)

    logger.info(
        "Search service readiness check: Redis %s, Kafka consumer %s",
        "healthy" if redis_ready else "unhealthy",
        "active" if kafka_ready else "inactive",
    )

    body = {
        "status": "ready" if is_ready else "not_ready",
        "service": settings.APP_NAME,
        "redis": redis_health,
        "kafka": kafka_health,
    }

    if not is_ready:
        return JSONResponse(status_code=503, content=body)

    return body
