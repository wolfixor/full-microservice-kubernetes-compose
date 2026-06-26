"""Search repository for Elasticsearch operations."""

import logging
from typing import List, Optional
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError

from ..models.search import (
    SearchDocument, 
    TaskSearchDocument, 
    CommentSearchDocument,
    SearchResponse
)
from ..core.elasticsearch_config import get_elasticsearch_client


class SearchRepository:
    """Repository for search operations."""
    
    def __init__(self):
        self.es_client: Optional[AsyncElasticsearch] = None
        self.index_name = "search_index"
        self.logger = logging.getLogger(__name__)
    
    async def _get_client(self) -> AsyncElasticsearch:
        """Get Elasticsearch client."""
        if self.es_client is None:
            self.es_client = await get_elasticsearch_client()
        return self.es_client
    
    async def initialize_index(self):
        """Initialize Elasticsearch index with mappings."""
        try:
            es_client = await self._get_client()
            
            # Check if index exists
            if await es_client.indices.exists(index=self.index_name):
                self.logger.info(f"Index {self.index_name} already exists")
                return
            
            # Create index with mappings
            index_body = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "default": {
                                "type": "standard"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "title": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "content": {"type": "text", "analyzer": "standard"},
                        "user_id": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "metadata": {"type": "object", "enabled": True},
                        "status": {"type": "keyword"},  # For tasks
                        "description": {"type": "text", "analyzer": "standard"},  # For tasks
                        "task_id": {"type": "keyword"}  # For comments
                    }
                }
            }
            
            await es_client.indices.create(
                index=self.index_name,
                body=index_body
            )
            self.logger.info(f"Created index {self.index_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize index: {e}")
            raise
    
    async def index_document(self, document: SearchDocument) -> bool:
        """Index a document in Elasticsearch."""
        try:
            es_client = await self._get_client()
            
            doc_dict = document.model_dump()
            
            # Index the document
            response = await es_client.index(
                index=self.index_name,
                id=document.id,
                body=doc_dict
            )
            
            self.logger.debug(f"Indexed document {document.id}: {response['result']}")
            return response['result'] == 'created' or response['result'] == 'updated'
            
        except Exception as e:
            self.logger.error(f"Failed to index document {document.id}: {e}")
            return False
    
    async def search(self, query: str, size: int = 20) -> SearchResponse:
        """Search for documents."""
        try:
            es_client = await self._get_client()
            
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content", "description"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"updated_at": {"order": "desc"}}
                ],
                "size": size
            }
            
            response = await es_client.search(
                index=self.index_name,
                body=search_body
            )
            
            # Parse results
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                source['id'] = hit['_id']
                
                if source['type'] == 'task':
                    results.append(TaskSearchDocument(**source))
                elif source['type'] == 'comment':
                    results.append(CommentSearchDocument(**source))
                else:
                    results.append(SearchDocument(**source))
            
            return SearchResponse(
                query=query,
                total=response['hits']['total']['value'],
                results=results
            )
            
        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {e}")
            return SearchResponse(query=query, total=0, results=[])
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the index."""
        try:
            es_client = await self._get_client()
            
            response = await es_client.delete(
                index=self.index_name,
                id=document_id
            )
            
            self.logger.debug(f"Deleted document {document_id}: {response['result']}")
            return response['result'] == 'deleted'
            
        except NotFoundError:
            self.logger.warning(f"Document {document_id} not found for deletion")
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def get_document(self, document_id: str) -> Optional[SearchDocument]:
        """Get a document by ID."""
        try:
            es_client = await self._get_client()
            
            response = await es_client.get(
                index=self.index_name,
                id=document_id
            )
            
            source = response['_source']
            source['id'] = response['_id']
            
            if source['type'] == 'task':
                return TaskSearchDocument(**source)
            elif source['type'] == 'comment':
                return CommentSearchDocument(**source)
            else:
                return SearchDocument(**source)
                
        except NotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    async def close(self):
        """Close Elasticsearch connection."""
        if self.es_client:
            await self.es_client.close()
            self.es_client = None