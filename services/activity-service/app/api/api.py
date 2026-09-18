"""Main API router configuration for activity service."""

from fastapi import APIRouter

from .endpoints import activities

api_router = APIRouter()
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
