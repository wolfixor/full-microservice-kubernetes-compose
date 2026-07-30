"""Kafka consumer for immutable activity records."""

import asyncio
import json
import logging
from typing import Optional

from .config import settings
from .event_mapper import activity_from_event
from ..db.session import AsyncSessionLocal
from ..repositories.activity_repository import ActivityRepository

logger = logging.getLogger(__name__)

ACTIVITY_EVENT_TOPICS = (
    "user.created",
    "user.updated",
    "task.created",
    "task.updated",
    "task.deleted",
    "comment.created",
    "comment.deleted",
)


def decode_event(value: bytes) -> Optional[dict]:
    """Decode a Kafka message value into a JSON event envelope."""
    try:
        event = json.loads(value.decode("utf-8"))
    except Exception as exc:
        logger.warning("Skipping non-JSON Kafka message: %s", exc)
        return None
    return event if isinstance(event, dict) else None


async def handle_event(event: dict) -> bool:
    """Persist a Kafka event as an activity row."""
    activity_data = activity_from_event(event)
    if not activity_data:
        logger.warning("Skipping Kafka message without activity fields: %s", event)
        return True

    async with AsyncSessionLocal() as session:
        repository = ActivityRepository(session)
        await repository.create(activity_data)
    return True


async def consume_activity_events(stop_event: asyncio.Event) -> None:
    """Consume business events and write immutable activities."""
    if not settings.KAFKA_ENABLED:
        logger.info("Kafka consumer disabled for activity-service")
        return

    from aiokafka import AIOKafkaConsumer

    consumer = AIOKafkaConsumer(
        *ACTIVITY_EVENT_TOPICS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP_ID,
        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
        enable_auto_commit=False,
    )

    await consumer.start()
    logger.info("Kafka consumer started for topics: %s", ", ".join(ACTIVITY_EVENT_TOPICS))

    try:
        while not stop_event.is_set():
            try:
                message = await asyncio.wait_for(consumer.getone(), timeout=1)
            except asyncio.TimeoutError:
                continue

            event = decode_event(message.value)
            if event is None:
                await consumer.commit()
                continue

            handled = await handle_event(event)
            if handled:
                await consumer.commit()
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")


def start_kafka_event_consumer() -> tuple[asyncio.Event, asyncio.Task]:
    """Start the Kafka event consumer in the background."""
    stop_event = asyncio.Event()
    task = asyncio.create_task(consume_activity_events(stop_event))
    return stop_event, task


async def stop_kafka_event_consumer(stop_event: asyncio.Event, task: asyncio.Task) -> None:
    """Stop the background Kafka event consumer."""
    stop_event.set()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
