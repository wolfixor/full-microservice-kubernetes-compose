"""Comment management endpoints."""

from typing import List
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ...db.session import get_db
from ...repositories.cached_comment_repository import CachedCommentRepository
from ...core.event_producer import publish_event

router = APIRouter()


def _comment_payload(comment) -> dict:
    return {
        "id": comment.id,
        "task_id": comment.task_id,
        "user_id": comment.user_id,
        "content": comment.content,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
    }


# Pydantic models
class CommentCreate(BaseModel):
    task_id: str = Field(..., description="ID of the task this comment belongs to")
    user_id: str = Field(..., description="ID of the user who created the comment")
    content: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[CommentResponse])
async def get_comments(
    db: AsyncSession = Depends(get_db)
):
    """Get all comments."""
    repository = CachedCommentRepository(db)
    comments = await repository.get_all()
    return comments


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get comment by ID."""
    repository = CachedCommentRepository(db)
    comment = await repository.get_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    return comment


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_create: CommentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new comment."""
    repository = CachedCommentRepository(db)
    
    comment = await repository.create(comment_create.dict())
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comment"
        )
    background_tasks.add_task(publish_event, "comment.created", comment.id, _comment_payload(comment))
    return comment


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_update: CommentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update a comment."""
    repository = CachedCommentRepository(db)
    
    comment = await repository.get_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    updated_comment = await repository.update(comment_id, comment_update.dict())
    return updated_comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Delete a comment."""
    repository = CachedCommentRepository(db)
    comment = await repository.get_by_id(comment_id)
    
    success = await repository.delete(comment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    if comment:
        background_tasks.add_task(publish_event, "comment.deleted", comment_id, _comment_payload(comment))
