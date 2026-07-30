"""Main notification service application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .api.api import api_router
from .core.config import settings
from .core.kafka_event_consumer import start_kafka_event_consumer, stop_kafka_event_consumer
from .core.log_context import LogContextMiddleware
from .core.logger import setup_logging
from .core.metrics import setup_metrics
from .db.session import async_engine

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    kafka_consumer = None
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logging.info("Database connection verified")
    except Exception as e:
        logging.warning(f"Database connection failed: {e}")

    try:
        kafka_consumer = start_kafka_event_consumer()
        logging.info("Kafka event consumer scheduled")
    except Exception as e:
        logging.warning(f"Kafka consumer startup failed: {e}")

    yield

    if kafka_consumer:
        await stop_kafka_event_consumer(*kafka_consumer)
    await async_engine.dispose()
    logging.info("Notification service shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=settings.ROOT_PATH,
    lifespan=lifespan,
)

app.add_middleware(LogContextMiddleware)
app.include_router(api_router, prefix="/api")
setup_metrics(app, async_engine)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint with database health check."""
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    return {
        "status": "ready" if db_connected else "not_ready",
        "service": settings.APP_NAME,
        "database": {"connected": db_connected},
    }
