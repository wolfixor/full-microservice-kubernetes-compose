"""Activity endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...repositories.activity_repository import ActivityRepository

router = APIRouter()


class ActivityResponse(BaseModel):
    """Activity API response model."""

    id: str
    event_id: str
    event_type: str
    source: str
    aggregate_id: str
    occurred_at: datetime
    payload: dict
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ActivityResponse])
async def get_activities(
    event_type: Optional[str] = None,
    aggregate_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return immutable business activity records."""
    repository = ActivityRepository(db)
    return await repository.list_activities(
        event_type=event_type,
        aggregate_id=aggregate_id,
        limit=limit,
        offset=offset,
    )
