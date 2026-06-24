"""Cached task repository with Redis integration."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models.task import Task, TaskStatus
from ..core.redis_config import redis_settings
from ..core.redis_utils import RedisCache, create_redis_client


class CachedTaskRepository:
    """Repository for task database operations with Redis caching."""
    
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
    
    def _get_cache_key(self, task_id: str) -> str:
        """Generate cache key for task."""
        return f"{self.key_prefix}{task_id}"
    
    async def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convert task model to dictionary for caching."""
        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "user_id": task.user_id,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }
    
    async def get_all(self) -> List[Task]:
        """Get all tasks (not cached)."""
        result = await self.db.execute(select(Task))
        return result.scalars().all()
    
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID with cache-aside pattern."""
        # Try Redis first
        await self._init_redis()
        
        cache_key = self._get_cache_key(task_id)
        cached_data = await self.redis_cache.get(cache_key)
        
        if cached_data:
            # Convert cached dict back to Task model
            # Parse datetime strings back to datetime objects
            if cached_data.get('created_at'):
                cached_data['created_at'] = datetime.fromisoformat(cached_data['created_at'])
            if cached_data.get('updated_at'):
                cached_data['updated_at'] = datetime.fromisoformat(cached_data['updated_at'])
            return Task(**cached_data)
        
        # Cache miss - query database
        result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if task:
            # Populate cache
            task_dict = await self._task_to_dict(task)
            await self.redis_cache.set(cache_key, task_dict, self.cache_ttl)
        
        return task
    
    async def get_by_user_id(self, user_id: str) -> List[Task]:
        """Get tasks by user ID (not cached due to collection pattern)."""
        result = await self.db.execute(
            select(Task).where(Task.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks by status (not cached due to collection pattern)."""
        result = await self.db.execute(
            select(Task).where(Task.status == status)
        )
        return result.scalars().all()
    
    async def create(self, task_data: dict) -> Optional[Task]:
        """Create a new task."""
        task = Task(**task_data)
        self.db.add(task)
        try:
            await self.db.commit()
            await self.db.refresh(task)
            return task
        except IntegrityError:
            await self.db.rollback()
            return None
    
    async def update(self, task_id: str, update_data: dict) -> Optional[Task]:
        """Update an existing task and invalidate cache."""
        # First, get the task from database to ensure it's attached to session
        result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        # Update task
        for field, value in update_data.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        await self.db.commit()
        await self.db.refresh(task)
        
        # Invalidate cache
        await self._init_redis()
        cache_key = self._get_cache_key(task_id)
        await self.redis_cache.delete(cache_key)
        
        return task
    
    async def delete(self, task_id: str) -> bool:
        """Delete a task by ID and invalidate cache."""
        # Get task first
        result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return False
        
        # Invalidate cache first
        await self._init_redis()
        cache_key = self._get_cache_key(task_id)
        await self.redis_cache.delete(cache_key)
        
        # Then delete from database
        await self.db.delete(task)
        await self.db.commit()
        return True