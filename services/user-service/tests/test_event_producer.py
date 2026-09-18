from datetime import datetime
import unittest

from app.core.event_producer import build_event, dead_letter_topic


class EventProducerTests(unittest.TestCase):
    def test_build_event_wraps_payload_with_event_metadata(self):
        event = build_event(
            event_type="user.created",
            source="user-service",
            payload={"id": "user-1", "email": "user@example.com"},
        )

        self.assertEqual(event["event_type"], "user.created")
        self.assertEqual(event["source"], "user-service")
        self.assertEqual(event["payload"], {"id": "user-1", "email": "user@example.com"})
        self.assertTrue(event["event_id"])
        datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))

    def test_dead_letter_topic_adds_dlq_suffix(self):
        self.assertEqual(dead_letter_topic("task.created"), "task.created.dlq")


if __name__ == "__main__":
    unittest.main()
