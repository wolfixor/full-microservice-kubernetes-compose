"""Main API router configuration for task service."""

from fastapi import APIRouter
from .endpoints import tasks

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])