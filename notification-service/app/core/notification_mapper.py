"""Map Kafka event envelopes into notifications."""

from typing import Any, Optional


def notification_from_event(event: Any) -> Optional[dict[str, Any]]:
    """Build a notification record dictionary from a supported Kafka event."""
    if not isinstance(event, dict):
        return None

    event_id = event.get("event_id")
    event_type = event.get("event_type")
    payload = event.get("payload") or {}

    if not event_id or not event_type:
        return None

    if event_type == "task.created":
        return _build_notification(
            event=event,
            user_id=payload.get("user_id"),
            notification_type="task_created",
            title="Task created",
            message=f"Task '{payload.get('title') or payload.get('id')}' was created.",
        )

    if event_type == "comment.created":
        return _build_notification(
            event=event,
            user_id=payload.get("user_id"),
            notification_type="comment_created",
            title="Comment created",
            message=f"New comment was created on task {payload.get('task_id')}.",
        )

    if event_type == "user.created":
        user_name = payload.get("name") or payload.get("email") or payload.get("id")
        return _build_notification(
            event=event,
            user_id=payload.get("id"),
            notification_type="user_created",
            title="User created",
            message=f"User {user_name} was created.",
        )

    return None


def _build_notification(
    event: dict[str, Any],
    user_id: Optional[str],
    notification_type: str,
    title: str,
    message: str,
) -> Optional[dict[str, Any]]:
    if not user_id:
        return None

    return {
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "source": event.get("source") or "unknown",
        "user_id": user_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "status": "unread",
        "payload": event.get("payload") or {},
        "occurred_at": event.get("occurred_at"),
    }
