"""Task repository for database operations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models.task import Task, TaskStatus


class TaskRepository:
    """Repository for task database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all(self) -> List[Task]:
        """Get all tasks."""
        result = await self.db.execute(select(Task))
        return result.scalars().all()
    
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: str) -> List[Task]:
        """Get tasks by user ID."""
        result = await self.db.execute(
            select(Task).where(Task.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks by status."""
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
    
    async def update(self, task: Task, update_data: dict) -> Task:
        """Update an existing task."""
        for field, value in update_data.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def delete(self, task_id: str) -> bool:
        """Delete a task by ID."""
        task = await self.get_by_id(task_id)
        if not task:
            return False
        
        await self.db.delete(task)
        await self.db.commit()
        return True