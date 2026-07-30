"""Database session management for notification service."""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..core.config import settings

sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
