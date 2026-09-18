"""Main API router configuration for user service."""

from fastapi import APIRouter
from .endpoints import users

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(users.router, prefix="/users", tags=["users"])