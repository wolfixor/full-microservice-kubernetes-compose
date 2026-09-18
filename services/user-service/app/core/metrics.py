"""Prometheus metrics instrumentation for user-service."""

from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import event

SERVICE_NAME = "user-service"

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
)

db_query_counter = Counter(
    "db_query_total",
    "Total number of database queries executed",
    ["service"]
)

db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Duration of database queries in seconds",
    ["service"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
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


def setup_metrics(app, async_engine=None):
    """Configure Prometheus metrics instrumentation."""
    instrumentator.instrument(app).expose(app)

    if async_engine:
        _setup_db_tracking(async_engine)


def _setup_db_tracking(async_engine):
    """Attach SQLAlchemy event listeners for query metrics."""
    sync_engine = async_engine.sync_engine

    @event.listens_for(sync_engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        db_query_counter.labels(service=SERVICE_NAME).inc()
