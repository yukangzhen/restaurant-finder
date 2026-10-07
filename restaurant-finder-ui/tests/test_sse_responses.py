import asyncio
import json
import unittest
from unittest.mock import patch

import app


class _Message:
    def __init__(self):
        self.content = ""
        self.streamed = []
        self.update_count = 0

    async def stream_token(self, text):
        self.streamed.append(text)

    async def update(self):
        self.update_count += 1


async def _async_lines(lines):
    for line in lines:
        yield line


class UIStreamResponseTests(unittest.TestCase):
    def invoke(self, lines):
        message = _Message()
        with (
            patch.object(app, "AGENT_CONNECTION_MODE", "aws"),
            patch.object(app, "AGENT_RUNTIME_ARN", "arn:aws:bedrock-agentcore:us-east-2:000000000000:runtime/test"),
            patch.object(app, "_aws_sse_lines", return_value=_async_lines(lines)),
        ):
            asyncio.run(app._invoke_agent(message, "hello", "Guest", "test-session"))
        return message

    def test_direct_block_message_survives_done(self):
        message = self.invoke([
            'data: {"blocked": true, "message": "Please ask about restaurant recommendations."}',
            'data: {"done": true}',
        ])

        self.assertEqual(message.content, "Please ask about restaurant recommendations.")
        self.assertNotEqual(message.content, "No response received.")
        self.assertGreaterEqual(message.update_count, 1)

    def test_nested_block_message_is_shown(self):
        nested = "data: " + json.dumps({"blocked": True, "message": "That request was blocked."})
        message = self.invoke(["data: " + json.dumps(nested), 'data: {"done": true}'])

        self.assertEqual(message.content, "That request was blocked.")

    def test_invalid_block_messages_use_safe_fallback(self):
        for value in (None, "", "  ", 17, {"text": "untrusted structure"}):
            with self.subTest(value=value):
                message = self.invoke(["data: " + json.dumps({"blocked": True, "message": value}), 'data: {"done": true}'])
                self.assertEqual(
                    message.content,
                    "I couldn't process that request. Please try a restaurant-related question.",
                )

    def test_normal_chunks_are_combined_and_streamed(self):
        message = self.invoke([
            "data: " + json.dumps({"chunk": "Hello "}),
            "data: " + json.dumps({"chunk": "there."}),
            'data: {"done": true}',
        ])

        self.assertEqual(message.streamed, ["Hello ", "there."])
        self.assertEqual(message.content, "Hello there.")

    def test_error_event_keeps_existing_error_display(self):
        message = self.invoke(["data: " + json.dumps({"error": "Runtime failed."}), 'data: {"done": true}'])

        self.assertEqual(message.content, "Error: Runtime failed.")

    def test_malformed_line_is_ignored_and_empty_stream_stays_explicit(self):
        message = self.invoke(["data: {malformed", 'data: {"done": true}'])

        self.assertEqual(message.content, "No response received.")


if __name__ == "__main__":
    unittest.main()
