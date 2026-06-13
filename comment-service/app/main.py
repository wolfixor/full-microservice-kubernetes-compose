"""Main comment service application."""

import logging
from fastapi import FastAPI
from .core.logger import setup_logging
from .core.config import settings
from .api.api import api_router

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    logger = logging.getLogger(__name__)
    logger.info("Comment service readiness check passed")
    
    return {
        "status": "ready",
        "service": settings.APP_NAME
    }