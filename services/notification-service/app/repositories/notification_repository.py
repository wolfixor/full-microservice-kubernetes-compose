"""Notification repository for database operations."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification import Notification


class NotificationRepository:
    """Repository for notification records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, notification_data: dict) -> Optional[Notification]:
        """Create a notification record, ignoring duplicate event IDs."""
        data = dict(notification_data)
        data["occurred_at"] = _parse_datetime(data.get("occurred_at"))

        notification = Notification(**data)
        self.db.add(notification)
        try:
            await self.db.commit()
            await self.db.refresh(notification)
            return notification
        except IntegrityError:
            await self.db.rollback()
            return None

    async def list_notifications(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """List notification records newest first."""
        query = select(Notification)

        if user_id:
            query = query.where(Notification.user_id == user_id)

        if status:
            query = query.where(Notification.status == status)

        if notification_type:
            query = query.where(Notification.type == notification_type)

        query = query.order_by(desc(Notification.occurred_at)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())


def _parse_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed

    return datetime.now(timezone.utc).replace(tzinfo=None)
