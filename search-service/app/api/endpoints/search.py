"""Search endpoints for search service."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...models.search import SearchResponse
from ...repositories.search_repository import SearchRepository

router = APIRouter()


# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str
    size: Optional[int] = 20


class IndexRequest(BaseModel):
    id: str
    type: str
    title: Optional[str] = None
    content: str
    user_id: str
    created_at: str
    updated_at: str
    metadata: dict = {}
    status: Optional[str] = None
    description: Optional[str] = None
    task_id: Optional[str] = None


@router.get("/", response_model=SearchResponse)
async def search(
    q: str,
    size: Optional[int] = 20
):
    """Search for documents."""
    repository = SearchRepository()
    
    if not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
    
    try:
        return await repository.search(q, size)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/index", status_code=status.HTTP_201_CREATED)
async def index_document(
    request: IndexRequest
):
    """Index a document for search."""
    repository = SearchRepository()
    
    try:
        # Create appropriate document based on type
        if request.type == "task":
            from ...models.search import TaskSearchDocument
            document = TaskSearchDocument(
                id=request.id,
                type=request.type,
                title=request.title,
                content=request.content,
                user_id=request.user_id,
                created_at=request.created_at,
                updated_at=request.updated_at,
                metadata=request.metadata,
                status=request.status or "pending",
                description=request.description or ""
            )
        elif request.type == "comment":
            from ...models.search import CommentSearchDocument
            document = CommentSearchDocument(
                id=request.id,
                type=request.type,
                title=request.title,
                content=request.content,
                user_id=request.user_id,
                created_at=request.created_at,
                updated_at=request.updated_at,
                metadata=request.metadata,
                task_id=request.task_id or ""
            )
        else:
            from ...models.search import SearchDocument
            document = SearchDocument(
                id=request.id,
                type=request.type,
                title=request.title,
                content=request.content,
                user_id=request.user_id,
                created_at=request.created_at,
                updated_at=request.updated_at,
                metadata=request.metadata
            )
        
        success = await repository.index_document(document)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to index document"
            )
        
        return {"message": "Document indexed successfully", "id": request.id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str):
    """Delete a document from the search index."""
    repository = SearchRepository()
    
    try:
        success = await repository.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/ingest/task/{task_id}", status_code=status.HTTP_200_OK)
async def ingest_task(task_id: str):
    """Ingest a task from task service."""
    from ...repositories.data_ingestor import DataIngestor
    
    ingestor = DataIngestor()
    
    try:
        success = await ingestor.ingest_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or ingestion failed"
            )
        
        return {"message": "Task ingested successfully", "task_id": task_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest task: {str(e)}"
        )


@router.post("/ingest/comment/{comment_id}", status_code=status.HTTP_200_OK)
async def ingest_comment(comment_id: str):
    """Ingest a comment from comment service."""
    from ...repositories.data_ingestor import DataIngestor
    
    ingestor = DataIngestor()
    
    try:
        success = await ingestor.ingest_comment(comment_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or ingestion failed"
            )
        
        return {"message": "Comment ingested successfully", "comment_id": comment_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest comment: {str(e)}"
        )


@router.post("/reindex/tasks", status_code=status.HTTP_200_OK)
async def reindex_all_tasks():
    """Reindex all tasks from task service."""
    from ...repositories.data_ingestor import DataIngestor
    
    ingestor = DataIngestor()
    
    try:
        success = await ingestor.reindex_all_tasks()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reindex tasks"
            )
        
        return {"message": "Tasks reindexing initiated"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex tasks: {str(e)}"
        )


@router.post("/reindex/comments", status_code=status.HTTP_200_OK)
async def reindex_all_comments():
    """Reindex all comments from comment service."""
    from ...repositories.data_ingestor import DataIngestor
    
    ingestor = DataIngestor()
    
    try:
        success = await ingestor.reindex_all_comments()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reindex comments"
            )
        
        return {"message": "Comments reindexing initiated"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex comments: {str(e)}"
        )