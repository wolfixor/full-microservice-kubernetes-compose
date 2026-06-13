"""Task management endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter()


# Enums and Pydantic models
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


# In-memory storage (temporary)
tasks_db = {}


@router.get("/", response_model=List[TaskResponse])
async def get_tasks():
    """Get all tasks."""
    return list(tasks_db.values())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task by ID."""
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_create: TaskCreate):
    """Create a new task."""
    import uuid
    
    task_id = str(uuid.uuid4())
    now = datetime.utcnow()
    task = TaskResponse(
        id=task_id,
        title=task_create.title,
        description=task_create.description,
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now
    )
    tasks_db[task_id] = task
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate):
    """Update a task."""
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task = tasks_db[task_id]
    update_data = task_update.dict(exclude_unset=True)
    
    # Update fields
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # Update timestamp
    task.updated_at = datetime.utcnow()
    
    tasks_db[task_id] = task
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str):
    """Delete a task."""
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    del tasks_db[task_id]