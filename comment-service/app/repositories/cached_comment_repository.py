"""Cached comment repository with Redis integration."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models.comment import Comment
from ..core.redis_config import redis_settings
from ..core.redis_utils import RedisCache, create_redis_client


class CachedCommentRepository:
    """Repository for comment database operations with Redis caching."""
    
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
    
    def _get_cache_key(self, comment_id: str) -> str:
        """Generate cache key for comment."""
        return f"{self.key_prefix}{comment_id}"
    
    async def _comment_to_dict(self, comment: Comment) -> Dict[str, Any]:
        """Convert comment model to dictionary for caching."""
        return {
            "id": str(comment.id),
            "task_id": comment.task_id,
            "user_id": comment.user_id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
        }
    
    async def get_all(self) -> List[Comment]:
        """Get all comments (not cached)."""
        result = await self.db.execute(select(Comment))
        return result.scalars().all()
    
    async def get_by_id(self, comment_id: str) -> Optional[Comment]:
        """Get comment by ID with cache-aside pattern."""
        # Try Redis first
        await self._init_redis()
        
        cache_key = self._get_cache_key(comment_id)
        cached_data = await self.redis_cache.get(cache_key)
        
        if cached_data:
            # Convert cached dict back to Comment model
            # Parse datetime strings back to datetime objects
            if cached_data.get('created_at'):
                cached_data['created_at'] = datetime.fromisoformat(cached_data['created_at'])
            if cached_data.get('updated_at'):
                cached_data['updated_at'] = datetime.fromisoformat(cached_data['updated_at'])
            return Comment(**cached_data)
        
        # Cache miss - query database
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        
        if comment:
            # Populate cache
            comment_dict = await self._comment_to_dict(comment)
            await self.redis_cache.set(cache_key, comment_dict, self.cache_ttl)
        
        return comment
    
    async def get_by_task_id(self, task_id: str) -> List[Comment]:
        """Get comments by task ID (not cached due to collection pattern)."""
        result = await self.db.execute(
            select(Comment).where(Comment.task_id == task_id)
        )
        return result.scalars().all()
    
    async def get_by_user_id(self, user_id: str) -> List[Comment]:
        """Get comments by user ID (not cached due to collection pattern)."""
        result = await self.db.execute(
            select(Comment).where(Comment.user_id == user_id)
        )
        return result.scalars().all()
    
    async def create(self, comment_data: dict) -> Optional[Comment]:
        """Create a new comment."""
        comment = Comment(**comment_data)
        self.db.add(comment)
        try:
            await self.db.commit()
            await self.db.refresh(comment)
            return comment
        except IntegrityError:
            await self.db.rollback()
            return None
    
    async def update(self, comment_id: str, update_data: dict) -> Optional[Comment]:
        """Update an existing comment and invalidate cache."""
        # First, get the comment from database to ensure it's attached to session
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            return None
        
        # Update comment
        for field, value in update_data.items():
            if hasattr(comment, field):
                setattr(comment, field, value)
        
        await self.db.commit()
        await self.db.refresh(comment)
        
        # Invalidate cache
        await self._init_redis()
        cache_key = self._get_cache_key(comment_id)
        await self.redis_cache.delete(cache_key)
        
        return comment
    
    async def delete(self, comment_id: str) -> bool:
        """Delete a comment by ID and invalidate cache."""
        # Get comment first
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            return False
        
        # Invalidate cache first
        await self._init_redis()
        cache_key = self._get_cache_key(comment_id)
        await self.redis_cache.delete(cache_key)
        
        # Then delete from database
        await self.db.delete(comment)
        await self.db.commit()
        return True