"""Comment repository for database operations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models.comment import Comment


class CommentRepository:
    """Repository for comment database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all(self) -> List[Comment]:
        """Get all comments."""
        result = await self.db.execute(select(Comment))
        return result.scalars().all()
    
    async def get_by_id(self, comment_id: str) -> Optional[Comment]:
        """Get comment by ID."""
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_task_id(self, task_id: str) -> List[Comment]:
        """Get comments by task ID."""
        result = await self.db.execute(
            select(Comment).where(Comment.task_id == task_id)
        )
        return result.scalars().all()
    
    async def get_by_user_id(self, user_id: str) -> List[Comment]:
        """Get comments by user ID."""
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
    
    async def update(self, comment: Comment, update_data: dict) -> Comment:
        """Update an existing comment."""
        for field, value in update_data.items():
            if hasattr(comment, field):
                setattr(comment, field, value)
        
        await self.db.commit()
        await self.db.refresh(comment)
        return comment
    
    async def delete(self, comment_id: str) -> bool:
        """Delete a comment by ID."""
        comment = await self.get_by_id(comment_id)
        if not comment:
            return False
        
        await self.db.delete(comment)
        await self.db.commit()
        return True