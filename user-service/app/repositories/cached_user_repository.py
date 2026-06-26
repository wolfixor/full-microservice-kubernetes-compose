"""Cached user repository with Redis integration."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models.user import User
from ..core.redis_config import redis_settings
from ..core.redis_utils import RedisCache, create_redis_client
from ..core.metrics import cache_hit_counter, cache_miss_counter


class CachedUserRepository:
    """Repository for user database operations with Redis caching."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_cache = None
        self.key_prefix = f"{redis_settings.REDIS_KEY_PREFIX}:"
        self.cache_ttl = redis_settings.CACHE_EXPIRE_SECONDS
    
    async def _init_redis(self):
        """Initialize Redis connection."""
        if not self.redis_cache:
            redis_client = await create_redis_client(
                host=redis_settings.REDIS_HOST,
                port=redis_settings.REDIS_PORT,
                db=redis_settings.REDIS_DB,
                password=redis_settings.REDIS_PASSWORD
            )
            self.redis_cache = RedisCache(redis_client)
    
    def _get_cache_key(self, user_id: str) -> str:
        """Generate cache key for user."""
        return f"{self.key_prefix}{user_id}"
    
    async def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert user model to dictionary for caching."""
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    
    async def get_all(self) -> List[User]:
        """Get all users (not cached)."""
        result = await self.db.execute(select(User))
        return result.scalars().all()
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID with cache-aside pattern."""
        # Try Redis first
        await self._init_redis()
        
        cache_key = self._get_cache_key(user_id)
        cached_data = await self.redis_cache.get(cache_key)
        
        if cached_data:
            cache_hit_counter.labels(service="user-service").inc()
            # Convert cached dict back to User model
            # Parse datetime strings back to datetime objects
            if cached_data.get('created_at'):
                cached_data['created_at'] = datetime.fromisoformat(cached_data['created_at'])
            if cached_data.get('updated_at'):
                cached_data['updated_at'] = datetime.fromisoformat(cached_data['updated_at'])
            return User(**cached_data)
        
        cache_miss_counter.labels(service="user-service").inc()
        # Cache miss - query database
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Populate cache
            user_dict = await self._user_to_dict(user)
            await self.redis_cache.set(cache_key, user_dict, self.cache_ttl)
        
        return user
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username (not cached due to lookup pattern)."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (not cached due to lookup pattern)."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_data: dict) -> Optional[User]:
        """Create a new user."""
        user = User(**user_data)
        self.db.add(user)
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError:
            await self.db.rollback()
            return None
    
    async def update(self, user_id: str, update_data: dict) -> Optional[User]:
        """Update an existing user and invalidate cache."""
        # First, get the user from database to ensure it's attached to session
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Update user
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        # Invalidate cache
        await self._init_redis()
        cache_key = self._get_cache_key(user_id)
        await self.redis_cache.delete(cache_key)
        
        return user
    
    async def delete(self, user_id: str) -> bool:
        """Delete a user by ID and invalidate cache."""
        # Get user first
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Invalidate cache first
        await self._init_redis()
        cache_key = self._get_cache_key(user_id)
        await self.redis_cache.delete(cache_key)
        
        # Then delete from database
        await self.db.delete(user)
        await self.db.commit()
        return True