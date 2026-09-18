"""Tests for mapping Kafka events into notifications."""

import unittest

from app.core.notification_mapper import notification_from_event


class NotificationMapperTest(unittest.TestCase):
    def test_maps_task_created_to_notification(self):
        event = {
            "event_id": "evt-1",
            "event_type": "task.created",
            "source": "task-service",
            "occurred_at": "2026-07-30T12:00:00Z",
            "payload": {
                "id": "task-1",
                "title": "Deploy Kafka",
                "user_id": "u1",
            },
        }

        notification = notification_from_event(event)

        self.assertEqual(notification["event_id"], "evt-1")
        self.assertEqual(notification["event_type"], "task.created")
        self.assertEqual(notification["user_id"], "u1")
        self.assertEqual(notification["type"], "task_created")
        self.assertEqual(notification["title"], "Task created")
        self.assertIn("Deploy Kafka", notification["message"])

    def test_maps_comment_created_to_notification(self):
        event = {
            "event_id": "evt-2",
            "event_type": "comment.created",
            "source": "comment-service",
            "occurred_at": "2026-07-30T12:01:00Z",
            "payload": {
                "id": "comment-1",
                "task_id": "task-1",
                "user_id": "u1",
                "content": "Looks good",
            },
        }

        notification = notification_from_event(event)

        self.assertEqual(notification["type"], "comment_created")
        self.assertEqual(notification["user_id"], "u1")
        self.assertIn("task-1", notification["message"])

    def test_ignores_unsupported_events(self):
        self.assertIsNone(notification_from_event("hello kafka"))
        self.assertIsNone(notification_from_event({"event_type": "task.deleted", "payload": {"id": "task-1"}}))


if __name__ == "__main__":
    unittest.main()
