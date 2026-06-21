"""Database session management for comment service."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from ..core.config import settings


# Synchronous engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    pool_size=5,  # Connection pool size
    max_overflow=10,  # Maximum overflow connections
    pool_pre_ping=True,  # Validate connections before using them
    echo=False  # Set to True for SQL debugging
)

# Asynchronous engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_size=5,  # Connection pool size
    max_overflow=10,  # Maximum overflow connections
    pool_pre_ping=True,  # Validate connections before using them
    echo=False  # Set to True for SQL debugging
)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """Get synchronous database session for migrations."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()