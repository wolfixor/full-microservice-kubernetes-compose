"""Tests for Kafka events consumed by the search service."""

import unittest

from app.core.kafka_event_consumer import (
    document_from_event,
    document_id_from_event,
    is_delete_event,
)
from app.models.search import CommentSearchDocument, TaskSearchDocument


class KafkaEventConsumerTest(unittest.TestCase):
    def test_builds_task_search_document_from_task_event(self):
        event = {
            "event_id": "evt-1",
            "event_type": "task.created",
            "source": "task-service",
            "payload": {
                "id": "task-1",
                "title": "Kafka test",
                "description": "event test",
                "status": "pending",
                "user_id": "u1",
                "created_at": "2026-07-27T10:40:02.850093",
                "updated_at": "2026-07-27T10:40:02.850096",
            },
        }

        document = document_from_event(event)

        self.assertIsInstance(document, TaskSearchDocument)
        self.assertEqual(document.id, "task-1")
        self.assertEqual(document.title, "Kafka test")
        self.assertEqual(document.content, "event test")
        self.assertEqual(document.metadata["event_type"], "task.created")

    def test_builds_comment_search_document_from_comment_event(self):
        event = {
            "event_id": "evt-2",
            "event_type": "comment.created",
            "source": "comment-service",
            "payload": {
                "id": "comment-1",
                "content": "Nice task",
                "task_id": "task-1",
                "user_id": "u1",
                "created_at": "2026-07-27T10:41:02.850093",
                "updated_at": "2026-07-27T10:41:02.850096",
            },
        }

        document = document_from_event(event)

        self.assertIsInstance(document, CommentSearchDocument)
        self.assertEqual(document.id, "comment-1")
        self.assertEqual(document.content, "Nice task")
        self.assertEqual(document.task_id, "task-1")

    def test_delete_event_uses_payload_id_without_document(self):
        event = {
            "event_type": "task.deleted",
            "payload": {"id": "task-1"},
        }

        self.assertTrue(is_delete_event(event["event_type"]))
        self.assertEqual(document_id_from_event(event), "task-1")
        self.assertIsNone(document_from_event(event))

    def test_ignores_non_event_messages(self):
        self.assertIsNone(document_id_from_event("ba salam"))
        self.assertIsNone(document_from_event("ba salam"))


if __name__ == "__main__":
    unittest.main()
