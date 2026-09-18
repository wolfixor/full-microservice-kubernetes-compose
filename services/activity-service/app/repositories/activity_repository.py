"""Activity repository for database operations."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.activity import Activity


class ActivityRepository:
    """Repository for immutable activity records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, activity_data: dict) -> Optional[Activity]:
        """Create an activity record, ignoring duplicate event IDs."""
        data = dict(activity_data)
        data["occurred_at"] = _parse_datetime(data.get("occurred_at"))

        activity = Activity(**data)
        self.db.add(activity)
        try:
            await self.db.commit()
            await self.db.refresh(activity)
            return activity
        except IntegrityError:
            await self.db.rollback()
            return None

    async def list_activities(
        self,
        event_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Activity]:
        """List activity records newest first."""
        query = select(Activity)

        if event_type:
            query = query.where(Activity.event_type == event_type)

        if aggregate_id:
            query = query.where(Activity.aggregate_id == aggregate_id)

        query = query.order_by(desc(Activity.occurred_at)).limit(limit).offset(offset)
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
