import asyncio
from contextlib import contextmanager
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import src.infrastructure.api  # Load packages in the same order as the app entrypoint.
from langchain_core.messages import AIMessage, HumanMessage

from src.application.orchestrator.workflow import edges
from src.application.orchestrator.workflow import nodes
from src.infrastructure import jev_router
from src.infrastructure.jev_router import JevRouterUnavailable


class _Span:
    def __init__(self, name):
        self.name = name
        self.attributes = {}

    def set_attribute(self, key, value):
        self.attributes[key] = value


class _Observability:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.spans = []
        self.steps = []

    @contextmanager
    def create_span(self, name, **_kwargs):
        span = _Span(name) if self.enabled else None
        if span is not None:
            self.spans.append(span)
        yield span

    def record_workflow_step(self, **kwargs):
        self.steps.append(kwargs)


class RouterNodeTests(unittest.TestCase):
    def run_router(self, jev_result=None, jev_error=None, bedrock_text=None, observability=None):
        observability = observability or _Observability()
        jev = AsyncMock()
        if jev_error is not None:
            jev.side_effect = jev_error
        else:
            jev.return_value = jev_result

        bedrock = SimpleNamespace(ainvoke=AsyncMock(return_value=AIMessage(content=bedrock_text or "")))
        with (
            patch.object(nodes, "get_observability_manager", return_value=observability),
            patch.object(nodes, "classify_with_jev", jev),
            patch.object(nodes, "get_router_chain", return_value=bedrock),
        ):
            state = asyncio.run(nodes.router_node({"messages": [HumanMessage(content="private input text")]}, {}))

        return state, observability, jev, bedrock

    def test_jev_success_sets_safe_provider_intent_attributes_without_bedrock(self):
        state, observability, jev, bedrock = self.run_router(
            jev_result=SimpleNamespace(intent="restaurant_search", confidence=0.91)
        )

        self.assertEqual(state["intent"], "restaurant_search")
        self.assertEqual(edges.route_by_intent(state), "search_agent")
        jev.assert_awaited_once()
        bedrock.ainvoke.assert_not_awaited()
        attributes = observability.spans[0].attributes
        self.assertEqual(attributes["router.intent"], "restaurant_search")
        self.assertEqual(attributes["router.provider"], "jev")
        self.assertEqual(attributes["router.model"], nodes.settings.JEV_ROUTER_MODEL)
        self.assertEqual(attributes["router.confidence"], 0.91)
        self.assertNotIn("private input text", str(attributes))
        self.assertEqual(observability.steps[0]["metadata"]["provider"], "jev")

    def test_disabled_observability_does_not_break_router(self):
        state, observability, _jev, _bedrock = self.run_router(
            jev_result=SimpleNamespace(intent="simple", confidence=None),
            observability=_Observability(enabled=False),
        )

        self.assertEqual(state["intent"], "simple")
        self.assertEqual(observability.steps[0]["metadata"]["provider"], "jev")
        self.assertEqual(observability.spans, [])

    def test_timeout_uses_bedrock_and_records_only_sanitized_failure_type(self):
        secret_text = "secret-provider-detail"
        observability = _Observability()
        with patch.object(nodes.logger, "warning") as warning:
            state, observability, jev, bedrock = self.run_router(
                jev_error=TimeoutError(secret_text),
                bedrock_text="simple",
                observability=observability,
            )

        self.assertEqual(state["intent"], "simple")
        jev.assert_awaited_once()
        bedrock.ainvoke.assert_awaited_once()
        attributes = observability.spans[0].attributes
        self.assertEqual(attributes["router.provider"], "bedrock")
        self.assertEqual(attributes["router.fallback.reason"], "TimeoutError")
        self.assertNotIn(secret_text, str(attributes))
        self.assertNotIn(secret_text, str(warning.call_args_list))

    def test_unavailable_or_rejected_jev_result_uses_bedrock(self):
        for failure in (
            JevRouterUnavailable("Jev client is not initialized"),
            JevRouterUnavailable("Jev returned an invalid intent"),
        ):
            with self.subTest(failure=str(failure)):
                state, observability, _jev, bedrock = self.run_router(
                    jev_error=failure, bedrock_text="simple"
                )
                self.assertEqual(state["intent"], "simple")
                bedrock.ainvoke.assert_awaited_once()
                self.assertEqual(
                    observability.spans[0].attributes["router.provider"], "bedrock"
                )

    def test_invalid_typed_jev_choice_is_rejected_before_routing(self):
        class _Client:
            async def system_one(self, **_kwargs):
                return SimpleNamespace(
                    choices={"intent": SimpleNamespace(choice="unknown", confidence=1.0)}
                )

        with patch.object(jev_router, "_jev_client", _Client()):
            with self.assertRaises(JevRouterUnavailable):
                asyncio.run(jev_router.classify_with_jev([HumanMessage(content="hello")]))

    def test_fallback_maps_each_supported_intent(self):
        for text, expected in (
            ("restaurant_search", "restaurant_search"),
            ("simple", "simple"),
            ("off_topic", "off_topic"),
        ):
            with self.subTest(text=text):
                state, observability, _jev, bedrock = self.run_router(
                    jev_error=RuntimeError("simulated failure"), bedrock_text=text
                )
                self.assertEqual(state["intent"], expected)
                bedrock.ainvoke.assert_awaited_once()
                self.assertEqual(observability.spans[0].attributes["router.provider"], "bedrock")

    def test_unrecognized_bedrock_text_is_not_written_to_logs_or_spans(self):
        secret_text = "secret-classifier-response"
        with patch.object(nodes.logger, "warning") as warning:
            state, observability, _jev, _bedrock = self.run_router(
                jev_error=RuntimeError("simulated failure"), bedrock_text=secret_text
            )

        self.assertEqual(state["intent"], "restaurant_search")
        self.assertNotIn(secret_text, str(warning.call_args_list))
        self.assertNotIn(secret_text, str([span.attributes for span in observability.spans]))


if __name__ == "__main__":
    unittest.main()
