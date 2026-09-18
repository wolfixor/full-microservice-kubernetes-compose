"""Notification endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...repositories.notification_repository import NotificationRepository

router = APIRouter()


class NotificationResponse(BaseModel):
    """Notification API response model."""

    id: str
    event_id: str
    event_type: str
    source: str
    user_id: str
    type: str
    title: str
    message: str
    status: str
    payload: dict
    occurred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return stored notification records."""
    repository = NotificationRepository(db)
    return await repository.list_notifications(
        user_id=user_id,
        status=status,
        notification_type=type,
        limit=limit,
        offset=offset,
    )
