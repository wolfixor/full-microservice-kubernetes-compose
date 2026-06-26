"""Prometheus metrics instrumentation for search-service."""

from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

SERVICE_NAME = "search-service"

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
)

es_query_counter = Counter(
    "es_query_total",
    "Total number of Elasticsearch queries executed",
    ["service"]
)

es_index_counter = Counter(
    "es_index_total",
    "Total number of Elasticsearch index operations",
    ["service"]
)

cache_hit_counter = Counter(
    "cache_hit_total",
    "Total number of Redis cache hits",
    ["service"]
)

cache_miss_counter = Counter(
    "cache_miss_total",
    "Total number of Redis cache misses",
    ["service"]
)


def setup_metrics(app):
    """Configure Prometheus metrics instrumentation."""
    instrumentator.instrument(app).expose(app)
