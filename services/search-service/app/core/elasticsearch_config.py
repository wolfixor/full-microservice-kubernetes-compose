"""Elasticsearch configuration for search service."""

from elasticsearch import AsyncElasticsearch
from .config import settings

_es_client: AsyncElasticsearch | None = None


async def get_elasticsearch_client() -> AsyncElasticsearch:
    """Get or create the singleton Elasticsearch client."""
    global _es_client
    if _es_client is None:
        client_kwargs = {
            "request_timeout": 30,
            "retry_on_timeout": True,
        }
        if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
            client_kwargs["basic_auth"] = (
                settings.ELASTICSEARCH_USERNAME,
                settings.ELASTICSEARCH_PASSWORD,
            )
        _es_client = AsyncElasticsearch(
            [settings.ELASTICSEARCH_URL],
            **client_kwargs,
        )
    return _es_client


async def close_elasticsearch_client():
    """Close the singleton Elasticsearch client."""
    global _es_client
    if _es_client is not None:
        await _es_client.close()
        _es_client = None
