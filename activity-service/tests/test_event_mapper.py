"""Tests for mapping Kafka envelopes into activity records."""

import unittest

from app.core.event_mapper import activity_from_event


class EventMapperTest(unittest.TestCase):
    def test_maps_task_event_to_activity_record(self):
        event = {
            "event_id": "evt-1",
            "event_type": "task.created",
            "source": "task-service",
            "occurred_at": "2026-07-30T10:00:00Z",
            "payload": {
                "id": "task-1",
                "title": "Kafka audit",
                "user_id": "u1",
            },
        }

        activity = activity_from_event(event)

        self.assertEqual(activity["event_id"], "evt-1")
        self.assertEqual(activity["event_type"], "task.created")
        self.assertEqual(activity["source"], "task-service")
        self.assertEqual(activity["aggregate_id"], "task-1")
        self.assertEqual(activity["payload"]["title"], "Kafka audit")

    def test_ignores_non_event_messages(self):
        self.assertIsNone(activity_from_event("hello kafka"))


if __name__ == "__main__":
    unittest.main()
