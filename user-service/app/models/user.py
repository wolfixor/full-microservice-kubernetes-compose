"""User model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class User(Base):
    """User model for user service."""
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    full_name: Mapped[str] = mapped_column(String(100), default="")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )