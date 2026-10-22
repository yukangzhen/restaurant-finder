import unittest

from src.application.orchestrator.identity import resolve_request_identity


class RequestIdentityTests(unittest.TestCase):
    def test_anonymous_actor_is_stable_for_a_conversation_and_isolated_between_them(self):
        first = resolve_request_identity("conversation-1", None)
        repeated = resolve_request_identity("conversation-1", None)
        other = resolve_request_identity("conversation-2", None)

        self.assertEqual(first.actor_id, repeated.actor_id)
        self.assertNotEqual(first.actor_id, other.actor_id)
        self.assertTrue(first.actor_id.startswith("anon:"))

    def test_explicit_actor_is_preserved(self):
        identity = resolve_request_identity("conversation_1", "account:user-42")

        self.assertEqual(identity.actor_id, "account:user-42")
        self.assertEqual(identity.conversation_id, "conversation_1")

    def test_invalid_session_or_actor_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_request_identity("bad session", None)
        with self.assertRaises(ValueError):
            resolve_request_identity("valid-session", "bad actor id")


if __name__ == "__main__":
    unittest.main()
