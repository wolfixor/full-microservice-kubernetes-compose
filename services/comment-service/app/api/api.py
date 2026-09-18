"""Main API router configuration for comment service."""

from fastapi import APIRouter
from .endpoints import comments

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])