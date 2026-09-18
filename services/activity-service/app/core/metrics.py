"""Prometheus metrics instrumentation for activity-service."""

from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import event

SERVICE_NAME = "activity-service"

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
)

db_query_counter = Counter(
    "activity_db_query_total",
    "Total number of activity-service database queries executed",
    ["service"],
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
