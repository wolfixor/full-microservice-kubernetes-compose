"""Prometheus metrics instrumentation for search-service."""

from prometheus_client import Counter, Gauge, Histogram
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

redis_health_gauge = Gauge(
    "search_service_redis_healthy",
    "Search service Redis health status: 1 healthy, 0 unhealthy",
    ["service"]
)

kafka_consumer_active_gauge = Gauge(
    "search_service_kafka_consumer_active",
    "Search service Kafka consumer status: 1 active, 0 inactive",
    ["service", "group_id"]
)

kafka_consumer_last_message_timestamp = Gauge(
    "search_service_kafka_consumer_last_message_timestamp_seconds",
    "Unix timestamp of the last Kafka message processed by search-service",
    ["service", "group_id"]
)

kafka_events_processed_counter = Counter(
    "search_service_kafka_events_processed_total",
    "Total Kafka events processed by search-service",
    ["service", "event_type"]
)

kafka_events_failed_counter = Counter(
    "search_service_kafka_events_failed_total",
    "Total Kafka events that search-service failed to process",
    ["service", "event_type"]
)


def setup_metrics(app):
    """Configure Prometheus metrics instrumentation."""
    instrumentator.instrument(app).expose(app)
