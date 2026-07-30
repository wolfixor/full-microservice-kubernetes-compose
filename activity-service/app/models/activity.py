"""Activity model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class Activity(Base):
    """Immutable audit record for one business event."""

    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    event_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
