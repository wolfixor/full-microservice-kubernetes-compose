"""Search models for Elasticsearch."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SearchDocument(BaseModel):
    """Base search document model."""
    id: str
    type: str = Field(description="Document type: task or comment")
    title: Optional[str] = None
    content: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class TaskSearchDocument(SearchDocument):
    """Task document for search index."""
    type: str = "task"
    status: str
    description: str


class CommentSearchDocument(SearchDocument):
    """Comment document for search index."""
    type: str = "comment"
    task_id: str


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    total: int
    results: list[SearchDocument]
    
    class Config:
        from_attributes = True