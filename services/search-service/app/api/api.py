"""Main API router configuration for search service."""

from fastapi import APIRouter
from .endpoints import search

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(search.router, prefix="/search", tags=["search"])