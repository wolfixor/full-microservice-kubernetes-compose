"""Kafka consumer for updating the search index from domain events."""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from ..core.config import settings
from ..core.metrics import (
    SERVICE_NAME,
    kafka_consumer_active_gauge,
    kafka_consumer_last_message_timestamp,
    kafka_events_failed_counter,
    kafka_events_processed_counter,
)
from ..models.search import CommentSearchDocument, SearchDocument, TaskSearchDocument

if TYPE_CHECKING:
    from ..repositories.search_repository import SearchRepository

logger = logging.getLogger(__name__)

kafka_consumer_state = {
    "enabled": settings.KAFKA_ENABLED,
    "active": False,
    "last_error": None,
}

SEARCH_EVENT_TOPICS = (
    "task.created",
    "task.updated",
    "task.deleted",
    "comment.created",
    "comment.deleted",
)


def _event_datetime(payload: dict, field: str) -> datetime | str:
    return payload.get(field) or datetime.now(timezone.utc)


def is_delete_event(event_type: str) -> bool:
    """Return true when the event should delete a search document."""
    return event_type in {"task.deleted", "comment.deleted"}


def document_id_from_event(event: dict) -> Optional[str]:
    """Extract the search document ID from an event payload."""
    if not isinstance(event, dict):
        return None

    payload = event.get("payload") or {}
    return payload.get("id")


def document_from_event(event: dict) -> Optional[SearchDocument]:
    """Build a search document from a task/comment Kafka event."""
    if not isinstance(event, dict):
        return None

    event_type = event.get("event_type")
    payload = event.get("payload") or {}
    metadata = {
        "event_id": event.get("event_id"),
        "event_type": event_type,
        "source": event.get("source"),
    }

    if is_delete_event(event_type):
        return None

    if event_type in {"task.created", "task.updated"}:
        description = payload.get("description") or ""
        title = payload.get("title") or ""
        return TaskSearchDocument(
            id=payload["id"],
            title=title,
            content=description or title,
            description=description,
            status=payload.get("status") or "unknown",
            user_id=payload.get("user_id") or "",
            created_at=_event_datetime(payload, "created_at"),
            updated_at=_event_datetime(payload, "updated_at"),
            metadata=metadata,
        )

    if event_type == "comment.created":
        return CommentSearchDocument(
            id=payload["id"],
            content=payload.get("content") or "",
            user_id=payload.get("user_id") or "",
            task_id=payload.get("task_id") or "",
            created_at=_event_datetime(payload, "created_at"),
            updated_at=_event_datetime(payload, "updated_at"),
            metadata=metadata,
        )

    return None


async def handle_event(event: dict, repository: "SearchRepository") -> bool:
    """Apply a Kafka event to Elasticsearch."""
    if not isinstance(event, dict):
        logger.warning("Skipping non-JSON-envelope Kafka message: %s", event)
        return True

    document_id = document_id_from_event(event)
    event_type = event.get("event_type")

    if not document_id:
        logger.warning("Skipping Kafka event without payload.id: %s", event)
        return True

    if is_delete_event(event_type):
        await repository.delete_document(document_id)
        return True

    document = document_from_event(event)
    if not document:
        logger.info("Skipping unsupported Kafka event type: %s", event_type)
        return True

    return await repository.index_document(document)


async def consume_search_events(stop_event: asyncio.Event) -> None:
    """Consume task/comment events and update Elasticsearch."""
    if not settings.KAFKA_ENABLED:
        logger.info("Kafka consumer disabled for search-service")
        kafka_consumer_state.update({"active": False, "last_error": None})
        return

    from aiokafka import AIOKafkaConsumer
    from ..repositories.search_repository import SearchRepository

    consumer = AIOKafkaConsumer(
        *SEARCH_EVENT_TOPICS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP_ID,
        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
        enable_auto_commit=False,
    )
    repository = SearchRepository()
    consumer_started = False

    try:
        await consumer.start()
        consumer_started = True
        kafka_consumer_state.update({"active": True, "last_error": None})
        kafka_consumer_active_gauge.labels(
            service=SERVICE_NAME,
            group_id=settings.KAFKA_CONSUMER_GROUP_ID,
        ).set(1)
        logger.info("Kafka consumer started for topics: %s", ", ".join(SEARCH_EVENT_TOPICS))

        while not stop_event.is_set():
            try:
                message = await asyncio.wait_for(consumer.getone(), timeout=1)
            except asyncio.TimeoutError:
                continue

            try:
                event = json.loads(message.value.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                kafka_events_failed_counter.labels(service=SERVICE_NAME, event_type="invalid_json").inc()
                kafka_consumer_state["last_error"] = f"Invalid Kafka message: {exc}"
                logger.warning(
                    "Skipping invalid Kafka message topic=%s partition=%s offset=%s error=%s",
                    message.topic,
                    message.partition,
                    message.offset,
                    exc,
                )
                await consumer.commit()
                continue

            event_type = event.get("event_type", "unknown") if isinstance(event, dict) else "unknown"
            try:
                indexed = await handle_event(event, repository)
            except Exception as exc:
                kafka_events_failed_counter.labels(service=SERVICE_NAME, event_type=event_type).inc()
                kafka_consumer_state["last_error"] = str(exc)
                logger.exception("Kafka event processing failed for event_type=%s", event_type)
                continue

            if indexed:
                await consumer.commit()
                kafka_events_processed_counter.labels(service=SERVICE_NAME, event_type=event_type).inc()
                kafka_consumer_last_message_timestamp.labels(
                    service=SERVICE_NAME,
                    group_id=settings.KAFKA_CONSUMER_GROUP_ID,
                ).set(time.time())
    except Exception as exc:
        kafka_consumer_state.update({"active": False, "last_error": str(exc)})
        kafka_consumer_active_gauge.labels(
            service=SERVICE_NAME,
            group_id=settings.KAFKA_CONSUMER_GROUP_ID,
        ).set(0)
        logger.exception("Kafka consumer crashed")
        raise
    finally:
        kafka_consumer_state["active"] = False
        kafka_consumer_active_gauge.labels(
            service=SERVICE_NAME,
            group_id=settings.KAFKA_CONSUMER_GROUP_ID,
        ).set(0)
        if consumer_started:
            await consumer.stop()
        await repository.close()
        logger.info("Kafka consumer stopped")


def start_kafka_event_consumer() -> tuple[asyncio.Event, asyncio.Task]:
    """Start the Kafka event consumer in the background."""
    stop_event = asyncio.Event()
    task = asyncio.create_task(consume_search_events(stop_event))
    return stop_event, task


def get_kafka_consumer_health() -> dict:
    """Return current Kafka consumer health for readiness checks."""
    if not settings.KAFKA_ENABLED:
        return {"enabled": False, "active": True, "message": "Kafka consumer disabled"}

    if kafka_consumer_state["active"]:
        return {"enabled": True, "active": True, "message": "Kafka consumer active"}

    return {
        "enabled": True,
        "active": False,
        "message": "Kafka consumer inactive",
        "last_error": kafka_consumer_state.get("last_error"),
    }


async def stop_kafka_event_consumer(stop_event: asyncio.Event, task: asyncio.Task) -> None:
    """Stop the background Kafka event consumer."""
    stop_event.set()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
