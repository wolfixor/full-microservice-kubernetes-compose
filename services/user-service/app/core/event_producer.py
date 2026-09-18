"""Async Kafka event publishing helpers."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from .config import settings

logger = logging.getLogger(__name__)
_producer: Optional[Any] = None


def build_event(event_type: str, source: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Build a standard event envelope."""
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "source": source,
        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "payload": payload,
    }


def dead_letter_topic(topic: str) -> str:
    """Return the dead-letter topic for a Kafka topic."""
    return f"{topic}.dlq"


async def _get_producer():
    global _producer
    if _producer is None:
        from aiokafka import AIOKafkaProducer

        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            client_id=settings.KAFKA_CLIENT_ID,
            acks="all",
            enable_idempotence=True,
            value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
            key_serializer=lambda value: value.encode("utf-8") if value else None,
        )
        await _producer.start()
    return _producer


async def _send(topic: str, key: str, event: dict[str, Any]) -> None:
    producer = await _get_producer()
    await producer.send_and_wait(topic, key=key, value=event)


async def publish_event(topic: str, key: str, payload: dict[str, Any]) -> bool:
    """Publish an event with retries and dead-letter fallback."""
    if not settings.KAFKA_ENABLED:
        logger.info("Kafka publishing disabled; skipped event %s", topic)
        return False

    event = build_event(topic, settings.APP_NAME, payload)
    last_error: Optional[Exception] = None

    for attempt in range(1, settings.KAFKA_PUBLISH_RETRIES + 1):
        try:
            await _send(topic, key, event)
            logger.info("Published Kafka event %s with key %s", topic, key)
            return True
        except Exception as exc:
            last_error = exc
            logger.warning("Kafka publish failed for %s attempt %s: %s", topic, attempt, exc)
            await asyncio.sleep(min(2 ** (attempt - 1), 5))

    dlq_event = {
        **event,
        "error": str(last_error) if last_error else "unknown publish error",
        "original_topic": topic,
    }
    try:
        await _send(dead_letter_topic(topic), key, dlq_event)
        logger.error("Published Kafka event %s to dead-letter topic", topic)
    except Exception as exc:
        logger.error("Failed to publish Kafka event %s to dead-letter topic: %s", topic, exc)

    return False


async def close_event_producer() -> None:
    """Close the singleton Kafka producer."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
