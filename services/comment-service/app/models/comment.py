"""Comment model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class Comment(Base):
    """Comment model for comment service."""
    
    __tablename__ = "comments"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )