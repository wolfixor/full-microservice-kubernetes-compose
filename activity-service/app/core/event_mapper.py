"""Map Kafka event envelopes into activity records."""

from typing import Any, Optional


def activity_from_event(event: Any) -> Optional[dict[str, Any]]:
    """Build an activity record dictionary from a Kafka event envelope."""
    if not isinstance(event, dict):
        return None

    payload = event.get("payload") or {}
    aggregate_id = payload.get("id")
    event_id = event.get("event_id")
    event_type = event.get("event_type")

    if not event_id or not event_type or not aggregate_id:
        return None

    return {
        "event_id": event_id,
        "event_type": event_type,
        "source": event.get("source") or "unknown",
        "aggregate_id": aggregate_id,
        "occurred_at": event.get("occurred_at"),
        "payload": payload,
    }
