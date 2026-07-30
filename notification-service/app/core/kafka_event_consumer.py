"""Kafka consumer for notification records."""

import asyncio
import json
import logging
from typing import Optional

from .config import settings
from .notification_mapper import notification_from_event
from ..db.session import AsyncSessionLocal
from ..repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)

NOTIFICATION_EVENT_TOPICS = (
    "user.created",
    "task.created",
    "comment.created",
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
    """Persist a Kafka event as a notification row."""
    notification_data = notification_from_event(event)
    if not notification_data:
        logger.info("Skipping Kafka event without notification mapping: %s", event)
        return True

    async with AsyncSessionLocal() as session:
        repository = NotificationRepository(session)
        await repository.create(notification_data)
    return True


async def consume_notification_events(stop_event: asyncio.Event) -> None:
    """Consume business events and write notifications."""
    if not settings.KAFKA_ENABLED:
        logger.info("Kafka consumer disabled for notification-service")
        return

    from aiokafka import AIOKafkaConsumer

    consumer = AIOKafkaConsumer(
        *NOTIFICATION_EVENT_TOPICS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP_ID,
        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
        enable_auto_commit=False,
    )

    await consumer.start()
    logger.info("Kafka consumer started for topics: %s", ", ".join(NOTIFICATION_EVENT_TOPICS))

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
    task = asyncio.create_task(consume_notification_events(stop_event))
    return stop_event, task


async def stop_kafka_event_consumer(stop_event: asyncio.Event, task: asyncio.Task) -> None:
    """Stop the background Kafka event consumer."""
    stop_event.set()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
