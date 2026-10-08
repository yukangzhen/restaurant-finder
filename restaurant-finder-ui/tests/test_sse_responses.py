import asyncio
import json
import threading
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

    def test_agentcore_invocation_and_stream_reads_run_off_the_event_loop_thread(self):
        event_loop_thread = threading.get_ident()

        class _Body:
            def __init__(self):
                self.iter_thread = None
                self.close_thread = None

            def iter_lines(self, chunk_size):
                self.iter_thread = threading.get_ident()
                self.chunk_size = chunk_size
                return iter([b'data: {"chunk":"safe"}', b'data: {"done":true}'])

            def close(self):
                self.close_thread = threading.get_ident()

        body = _Body()

        class _Client:
            invoke_thread = None
            kwargs = None

            def invoke_agent_runtime(self, **kwargs):
                self.invoke_thread = threading.get_ident()
                self.kwargs = kwargs
                return {"contentType": "text/event-stream", "response": body}

        client = _Client()

        async def collect():
            return [line async for line in app._aws_sse_lines({"prompt": "hello"}, "session-1")]

        with patch.object(app, "_get_agentcore_client", return_value=client):
            lines = asyncio.run(collect())

        self.assertEqual(len(lines), 2)
        self.assertNotEqual(client.invoke_thread, event_loop_thread)
        self.assertNotEqual(body.iter_thread, event_loop_thread)
        self.assertNotEqual(body.close_thread, event_loop_thread)
        self.assertEqual(body.chunk_size, 1)
        self.assertEqual(client.kwargs["runtimeSessionId"], "session-1")

    def test_agentcore_client_has_bounded_timeouts_and_no_retries(self):
        import boto3

        previous_client = app._agentcore_client
        app._agentcore_client = None
        try:
            with patch.object(boto3, "client", return_value=object()) as make_client:
                app._get_agentcore_client()
            config = make_client.call_args.kwargs["config"]
            self.assertEqual(config.connect_timeout, 10)
            self.assertEqual(config.read_timeout, 300)
            self.assertEqual(config.retries["total_max_attempts"], 1)
        finally:
            app._agentcore_client = previous_client


if __name__ == "__main__":
    unittest.main()
