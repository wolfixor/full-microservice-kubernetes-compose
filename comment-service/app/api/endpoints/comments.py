"""Comment management endpoints."""

from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


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


# In-memory storage (temporary)
comments_db = {}


@router.get("/", response_model=List[CommentResponse])
async def get_comments():
    """Get all comments."""
    return list(comments_db.values())


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(comment_id: str):
    """Get comment by ID."""
    comment = comments_db.get(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    return comment


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(comment_create: CommentCreate):
    """Create a new comment."""
    import uuid
    
    comment_id = str(uuid.uuid4())
    now = datetime.utcnow()
    comment = CommentResponse(
        id=comment_id,
        task_id=comment_create.task_id,
        user_id=comment_create.user_id,
        content=comment_create.content,
        created_at=now,
        updated_at=now
    )
    comments_db[comment_id] = comment
    return comment


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(comment_id: str, comment_update: CommentCreate):
    """Update a comment."""
    if comment_id not in comments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    now = datetime.utcnow()
    comment = CommentResponse(
        id=comment_id,
        task_id=comment_update.task_id,
        user_id=comment_update.user_id,
        content=comment_update.content,
        created_at=comments_db[comment_id].created_at,
        updated_at=now
    )
    comments_db[comment_id] = comment
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: str):
    """Delete a comment."""
    if comment_id not in comments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    del comments_db[comment_id]