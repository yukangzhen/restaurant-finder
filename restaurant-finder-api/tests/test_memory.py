import unittest
from datetime import datetime, timezone

from src.infrastructure.memory import MemoryRetrievalResult, ShortTermMemory


class _MemoryClient:
    def __init__(self):
        self.events = []

    def create_event(self, **kwargs):
        self.events.append(kwargs)
        return {"eventId": "event-1"}

    def retrieve_memory_records(self, *, memoryId, namespace, searchCriteria):
        if namespace.endswith("/facts"):
            raise PermissionError("not logged in")
        return {
            "memoryRecordSummaries": [
                {"content": {"text": f"record from {namespace}"}}
            ]
        }


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.memory = ShortTermMemory.__new__(ShortTermMemory)
        self.memory._memory_id = "memory-1"
        self.memory._client = _MemoryClient()

    def test_turn_event_uses_two_messages_and_repeatable_idempotency_token(self):
        args = {
            "actor_id": "account:user-1",
            "session_id": "session-1",
            "user_input": "Find Thai food",
            "agent_response": "Here are three places.",
            "user_message_id": "user-message-1",
            "assistant_message_id": "assistant-message-1",
            "event_timestamp": datetime(2026, 10, 7, tzinfo=timezone.utc),
        }

        first = self.memory.process_turn(**args)
        second = self.memory.process_turn(**args)

        self.assertTrue(first["success"])
        self.assertTrue(second["success"])
        self.assertEqual(self.memory._client.events[0]["clientToken"], self.memory._client.events[1]["clientToken"])
        self.assertEqual(
            [item["conversational"]["role"] for item in self.memory._client.events[0]["payload"]],
            ["USER", "ASSISTANT"],
        )

    def test_retrieval_reports_empty_results_separately_from_errors(self):
        result = self.memory.retrieve_specific_memories(
            query="Thai",
            actor_id="account:user-1",
            session_id="session-1",
            memory_types=["preferences", "facts"],
            top_k=3,
        )

        self.assertIsInstance(result, MemoryRetrievalResult)
        self.assertEqual(len(result.memories["preferences"]), 1)
        self.assertEqual(result.memories["facts"], [])
        self.assertEqual(result.errors["facts"], "PermissionError")


if __name__ == "__main__":
    unittest.main()
