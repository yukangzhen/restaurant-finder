import asyncio
from contextlib import contextmanager
import unittest
from unittest.mock import patch

import src.infrastructure.api  # Load packages in the same order as the app entrypoint.
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.application.orchestrator.workflow.nodes import memory_post_hook


class _Observability:
    @contextmanager
    def create_span(self, *_args, **_kwargs):
        yield None

    def add_span_event(self, *_args, **_kwargs):
        pass

    def record_memory_operation(self, *_args, **_kwargs):
        pass

    def record_workflow_step(self, *_args, **_kwargs):
        pass


class _Memory:
    def __init__(self):
        self.saved = None

    def process_turn(self, **kwargs):
        self.saved = kwargs
        return {"success": True}


class MemoryPostHookTests(unittest.TestCase):
    def test_saves_only_the_latest_user_message_and_final_assistant_answer(self):
        memory = _Memory()
        messages = [
            HumanMessage(content="Earlier request", id="user-old"),
            AIMessage(content="Earlier answer", id="assistant-old"),
            HumanMessage(
                content="Latest request",
                id="user-latest",
                additional_kwargs={
                    "agentcore_event_timestamp": "2026-10-07T02:00:00+00:00"
                },
            ),
            AIMessage(
                content="",
                tool_calls=[{"id": "call-1", "name": "search", "args": {}}],
            ),
            ToolMessage(content="tool result", tool_call_id="call-1"),
            AIMessage(content="Latest answer", id="assistant-latest"),
        ]
        config = {
            "configurable": {
                "actor_id": "account:user-1",
                "thread_id": "conversation-1",
            }
        }

        with (
            patch(
                "src.application.orchestrator.workflow.nodes.get_memory_instance",
                return_value=memory,
            ),
            patch(
                "src.application.orchestrator.workflow.nodes.get_observability_manager",
                return_value=_Observability(),
            ),
        ):
            asyncio.run(memory_post_hook({"messages": messages, "response_status": "approved"}, config))

        self.assertEqual(memory.saved["user_input"], "Latest request")
        self.assertEqual(memory.saved["agent_response"], "Latest answer")
        self.assertEqual(memory.saved["user_message_id"], "user-latest")
        self.assertEqual(memory.saved["assistant_message_id"], "assistant-latest")
        self.assertEqual(memory.saved["actor_id"], "account:user-1")


if __name__ == "__main__":
    unittest.main()
