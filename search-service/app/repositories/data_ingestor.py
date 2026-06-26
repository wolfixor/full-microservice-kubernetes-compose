"""Simple data ingestion simulator for search service."""

import logging
import httpx
from typing import Optional
from datetime import datetime

from ..core.config import settings
from .search_repository import SearchRepository


class DataIngestor:
    """Simple data ingestor for simulating event ingestion."""
    
    def __init__(self):
        self.search_repo = SearchRepository()
        self.logger = logging.getLogger(__name__)
    
    async def ingest_task(self, task_id: str) -> bool:
        """Ingest a task from task service."""
        try:
            async with httpx.AsyncClient() as client:
                # Fetch task from task service
                response = await client.get(
                    f"{settings.TASK_SERVICE_URL}/api/tasks/{task_id}",
                    timeout=10
                )
                
                if response.status_code != 200:
                    self.logger.warning(f"Task {task_id} not found: {response.status_code}")
                    return False
                
                task = response.json()
                
                # Index in Elasticsearch
                from ..models.search import TaskSearchDocument
                
                document = TaskSearchDocument(
                    id=task_id,
                    type="task",
                    title=task.get("title", ""),
                    content=task.get("description", ""),
                    user_id=task.get("user_id", ""),
                    created_at=task.get("created_at", datetime.utcnow().isoformat()),
                    updated_at=task.get("updated_at", datetime.utcnow().isoformat()),
                    metadata={"source": "task-service"},
                    status=task.get("status", "pending"),
                    description=task.get("description", "")
                )
                
                success = await self.search_repo.index_document(document)
                self.logger.info(f"Task {task_id} ingested: {success}")
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to ingest task {task_id}: {e}")
            return False
    
    async def ingest_comment(self, comment_id: str) -> bool:
        """Ingest a comment from comment service."""
        try:
            async with httpx.AsyncClient() as client:
                # Fetch comment from comment service
                response = await client.get(
                    f"{settings.COMMENT_SERVICE_URL}/api/comments/{comment_id}",
                    timeout=10
                )
                
                if response.status_code != 200:
                    self.logger.warning(f"Comment {comment_id} not found: {response.status_code}")
                    return False
                
                comment = response.json()
                
                # Index in Elasticsearch
                from ..models.search import CommentSearchDocument
                
                document = CommentSearchDocument(
                    id=comment_id,
                    type="comment",
                    title="",  # Comments don't have titles
                    content=comment.get("content", ""),
                    user_id=comment.get("user_id", ""),
                    created_at=comment.get("created_at", datetime.utcnow().isoformat()),
                    updated_at=comment.get("updated_at", datetime.utcnow().isoformat()),
                    metadata={"source": "comment-service"},
                    task_id=comment.get("task_id", "")
                )
                
                success = await self.search_repo.index_document(document)
                self.logger.info(f"Comment {comment_id} ingested: {success}")
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to ingest comment {comment_id}: {e}")
            return False
    
    async def delete_document(self, document_id: str, doc_type: str) -> bool:
        """Delete a document from search index."""
        try:
            success = await self.search_repo.delete_document(document_id)
            self.logger.info(f"Document {document_id} ({doc_type}) deleted: {success}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def reindex_all_tasks(self) -> bool:
        """Reindex all tasks from task service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.TASK_SERVICE_URL}/api/tasks/",
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch tasks: {response.status_code}")
                    return False
                
                tasks = response.json()
                success_count = 0
                
                for task in tasks:
                    if await self.ingest_task(task.get("id")):
                        success_count += 1
                
                self.logger.info(f"Reindexed {success_count}/{len(tasks)} tasks")
                return len(tasks) == 0 or success_count > 0
                
        except Exception as e:
            self.logger.error(f"Failed to reindex tasks: {e}")
            return False
    
    async def reindex_all_comments(self) -> bool:
        """Reindex all comments from comment service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.COMMENT_SERVICE_URL}/api/comments/",
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch comments: {response.status_code}")
                    return False
                
                comments = response.json()
                success_count = 0
                
                for comment in comments:
                    if await self.ingest_comment(comment.get("id")):
                        success_count += 1
                
                self.logger.info(f"Reindexed {success_count}/{len(comments)} comments")
                return len(comments) == 0 or success_count > 0
                
        except Exception as e:
            self.logger.error(f"Failed to reindex comments: {e}")
            return False