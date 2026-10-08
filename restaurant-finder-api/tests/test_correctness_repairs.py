import asyncio
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from src.application.orchestrator import streaming as orchestrator_streaming
from src.application.orchestrator.workflow import edges, nodes, tools
from src.domain.models import RestaurantSearchResult
from src.domain.restaurant_results import (
    RestaurantDataError,
    normalize_restaurant_response,
    parse_restaurant,
    parse_search_result,
)
from src.infrastructure import guardrails
from src.infrastructure import browser
from src.infrastructure.streaming import stream_response
from src.infrastructure.guardrails import GuardrailResult, GuardrailUnavailableError


class _Observability:
    @contextmanager
    def create_span(self, *_args, **_kwargs):
        yield None

    @contextmanager
    def session_context(self, *_args, **_kwargs):
        yield None

    def add_span_event(self, *_args, **_kwargs):
        pass

    def record_workflow_step(self, *_args, **_kwargs):
        pass


class RestaurantResponseNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "restaurants": [
                {
                    "name": "Zero Point Noodle House",
                    "rating": 0,
                    "review_count": 0,
                    "price": "$10–20",
                    "reservation_available": "false",
                }
            ],
            "data_source": "google_local",
        }

    def test_direct_dictionary_json_and_mcp_envelope_share_one_normalizer(self):
        variants = (
            self.payload,
            json.dumps(self.payload),
            [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "statusCode": 200,
                            "body": json.dumps({"result": self.payload}),
                        }
                    ),
                }
            ],
        )
        for raw in variants:
            with self.subTest(raw_type=type(raw).__name__):
                result = parse_search_result(raw, "noodles", {"location": "Penang"})
                self.assertEqual(result.total_results, 1)
                self.assertEqual(result.status, "success")
                restaurant = result.restaurants[0]
                self.assertEqual(restaurant.rating, 0)
                self.assertEqual(restaurant.review_count, 0)
                self.assertEqual(restaurant.price_range, None)
                self.assertEqual(restaurant.price_description, "$10–20")
                self.assertIs(restaurant.reservation_available, False)
                self.assertIsNone(restaurant.city)

    def test_missing_fields_stay_unknown_and_string_booleans_are_not_truthy(self):
        restaurant = parse_restaurant(
            {"name": "A Restaurant", "reservation_available": "false"}
        )
        self.assertIsNone(restaurant.rating)
        self.assertIsNone(restaurant.review_count)
        self.assertIsNone(restaurant.price_range)
        self.assertIsNone(restaurant.cuisine_type)
        self.assertIs(restaurant.reservation_available, False)
        self.assertIsNone(parse_restaurant({"name": "B", "reservation_available": "unknown"}).reservation_available)

    def test_zero_values_are_preserved_and_invalid_counts_are_null(self):
        restaurant = parse_restaurant(
            {"name": "A", "rating": 0, "review_count": "-4", "price_range": "$$"}
        )
        self.assertEqual(restaurant.rating, 0)
        self.assertIsNone(restaurant.review_count)
        self.assertEqual(restaurant.price_range.value, "$$")

    def test_http_and_provider_errors_are_typed_and_sanitized(self):
        with self.assertRaises(RestaurantDataError) as caught:
            normalize_restaurant_response({"statusCode": 502, "body": "private provider body"})
        self.assertEqual(caught.exception.code, "provider_http_error")
        self.assertNotIn("private provider body", str(caught.exception))

        result = parse_search_result(
            {
                "status": "error",
                "error": "secret response body",
                "error_code": "secret provider body",
            },
            "search",
        )
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_code, "provider_error")
        self.assertNotIn("secret", result.model_dump_json())

    def test_generic_web_pages_are_sources_not_restaurant_records(self):
        result = parse_search_result(
            {
                "restaurants": [{"title": "A guide to Thai food", "url": "https://example.test"}],
                "web_sources": [{"title": "Thai food guide", "url": "https://example.test"}],
                "data_source": "web_search",
            },
            "Thai food in Penang",
        )
        self.assertEqual(result.total_results, 0)
        self.assertEqual(result.status, "empty")
        self.assertEqual(result.web_sources[0]["url"], "https://example.test")

    def test_more_than_four_nested_envelopes_is_rejected(self):
        response = self.payload
        for _ in range(5):
            response = {"body": response}
        with self.assertRaises(RestaurantDataError) as caught:
            normalize_restaurant_response(response)
        self.assertEqual(caught.exception.code, "invalid_response")

    def test_lambda_local_data_does_not_copy_requested_filters_into_facts(self):
        repo_root = Path(__file__).resolve().parents[2]
        handler_path = repo_root / "restaurant-finder-infra" / "mcp" / "lambda" / "handler.py"
        spec = importlib.util.spec_from_file_location("restaurant_search_lambda_handler", handler_path)
        handler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(handler)

        records = handler._parse_local_results(
            api_response={"local_results": [{"title": "Verified Noodles", "rating": 0, "reviews": 0, "price": "$10–20"}]},
            location="Penang",
            cuisine="Thai",
            price_range="$$",
            limit=5,
        )
        self.assertEqual(records[0]["name"], "Verified Noodles")
        self.assertIsNone(records[0]["city"])
        self.assertIsNone(records[0]["cuisine_type"])
        self.assertEqual(records[0]["rating"], 0)
        self.assertEqual(records[0]["review_count"], 0)
        self.assertIsNone(records[0]["price_range"])
        self.assertEqual(records[0]["price_description"], "$10–20")

    def test_lambda_organic_pages_are_sources_not_restaurant_records(self):
        repo_root = Path(__file__).resolve().parents[2]
        handler_path = repo_root / "restaurant-finder-infra" / "mcp" / "lambda" / "handler.py"
        spec = importlib.util.spec_from_file_location("restaurant_search_lambda_handler", handler_path)
        handler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(handler)

        sources = handler._parse_web_results(
            {"organic_results": [{"title": "A Thai food guide", "link": "https://example.test/guide", "snippet": "An article"}]},
            location="Penang",
            cuisine="Thai",
            price_range="$$",
            limit=5,
        )
        self.assertEqual(sources, [{"title": "A Thai food guide", "snippet": "An article", "url": "https://example.test/guide"}])


class GuardrailSafetyTests(unittest.TestCase):
    def test_anonymized_output_is_allowed_only_with_returned_mask(self):
        response = {
            "action": "GUARDRAIL_INTERVENED",
            "outputs": [{"text": "Call [PHONE]"}],
            "assessments": [
                {"sensitiveInformationPolicy": {"piiEntities": [{"action": "ANONYMIZED"}]}}
            ],
        }
        with (
            patch.object(guardrails.settings, "GUARDRAIL_ENABLED", True),
            patch.object(guardrails, "get_guardrail_manager", return_value=SimpleNamespace(guardrail_id="g", guardrail_version="1")),
            patch.object(guardrails.boto3, "client", return_value=SimpleNamespace(apply_guardrail=lambda **_: response)),
        ):
            result = guardrails.apply_output_guardrail("Call 555-0100")
        self.assertTrue(result.allowed)
        self.assertEqual(result.output, "Call [PHONE]")

    def test_block_takes_precedence_over_anonymization(self):
        response = {
            "action": "GUARDRAIL_INTERVENED",
            "outputs": [{"text": "masked"}],
            "assessments": [
                {"sensitiveInformationPolicy": {"piiEntities": [{"action": "ANONYMIZED"}]}}
            , {"contentPolicy": {"filters": [{"action": "BLOCKED"}]}}],
        }
        with (
            patch.object(guardrails.settings, "GUARDRAIL_ENABLED", True),
            patch.object(guardrails, "get_guardrail_manager", return_value=SimpleNamespace(guardrail_id="g", guardrail_version="1")),
            patch.object(guardrails.boto3, "client", return_value=SimpleNamespace(apply_guardrail=lambda **_: response)),
        ):
            result = guardrails.apply_output_guardrail("unsafe")
        self.assertFalse(result.allowed)

    def test_enabled_but_unavailable_guardrail_fails_closed(self):
        with (
            patch.object(guardrails.settings, "GUARDRAIL_ENABLED", True),
            patch.object(guardrails, "get_guardrail_manager", return_value=SimpleNamespace(guardrail_id=None)),
        ):
            with self.assertRaises(GuardrailUnavailableError):
                guardrails.apply_input_guardrail("hello")

    def test_output_finalizer_replaces_existing_message_id_with_masked_text(self):
        messages = [HumanMessage(content="hello", id="user-1"), AIMessage(content="Call 555-0100", id="assistant-1")]
        with (
            patch.object(nodes, "get_observability_manager", return_value=_Observability()),
            patch.object(nodes, "apply_output_guardrail", return_value=GuardrailResult(True, "Call [PHONE]", "GUARDRAIL_INTERVENED")),
        ):
            state = asyncio.run(nodes.output_guardrail_node({"messages": messages}, {}))
        self.assertEqual(state["response_status"], "approved")
        self.assertEqual(state["messages"].id, "assistant-1")
        self.assertEqual(state["messages"].content, "Call [PHONE]")


class TurnLifecycleTests(unittest.TestCase):
    def test_fourth_pending_tool_call_is_executed(self):
        state = {"messages": [AIMessage(content="", tool_calls=[{"id": "call-4", "name": "lookup", "args": {}}])], "tool_call_count": 4}
        self.assertEqual(edges.should_continue_search_agent(state), "tools")

    def test_agent_trims_parallel_calls_to_remaining_turn_budget(self):
        response = AIMessage(
            content="",
            tool_calls=[
                {"id": "call-1", "name": "lookup", "args": {}},
                {"id": "call-2", "name": "lookup", "args": {}},
            ],
        )
        chain = SimpleNamespace(
            chain=SimpleNamespace(ainvoke=AsyncMock(return_value=response)),
            prompt_metadata=SimpleNamespace(name="search", version="1", id="p"),
        )
        with (
            patch.object(nodes, "get_observability_manager", return_value=_Observability()),
            patch.object(nodes, "get_search_agent_chain", return_value=chain) as get_chain,
        ):
            output = asyncio.run(
                nodes.search_agent_node(
                    {"messages": [HumanMessage(content="find food")], "tool_call_count": 3},
                    {},
                )
            )
        self.assertEqual(output["tool_call_count"], 4)
        self.assertEqual(len(output["messages"].tool_calls), 1)
        self.assertTrue(get_chain.call_args.kwargs["allow_tool_calls"])

    def test_tool_calls_are_disabled_after_the_fourth_call(self):
        chain = SimpleNamespace(
            chain=SimpleNamespace(ainvoke=AsyncMock(return_value=AIMessage(content="Here are the results."))),
            prompt_metadata=SimpleNamespace(name="search", version="1", id="p"),
        )
        with (
            patch.object(nodes, "get_observability_manager", return_value=_Observability()),
            patch.object(nodes, "get_search_agent_chain", return_value=chain) as get_chain,
        ):
            output = asyncio.run(
                nodes.search_agent_node(
                    {"messages": [HumanMessage(content="find food")], "tool_call_count": 4},
                    {},
                )
            )
        self.assertEqual(output["tool_call_count"], 4)
        self.assertFalse(get_chain.call_args.kwargs["allow_tool_calls"])

    def test_new_turn_resets_tool_budget_and_graph_runs_once(self):
        graph = SimpleNamespace(
            ainvoke=AsyncMock(
                return_value={
                    "messages": [HumanMessage(content="hi"), AIMessage(content="Hello.")],
                    "response_status": "approved",
                }
            )
        )
        with patch.object(orchestrator_streaming, "create_orchestrator_graph", return_value=graph):
            first = asyncio.run(
                orchestrator_streaming.run_orchestrator_turn("first", conversation_id="same-session", actor_id="actor-1")
            )
            second = asyncio.run(
                orchestrator_streaming.run_orchestrator_turn("second", conversation_id="same-session", actor_id="actor-1")
            )
        self.assertEqual(first.text, "Hello.")
        self.assertEqual(second.text, "Hello.")
        self.assertEqual(graph.ainvoke.await_count, 2)
        self.assertTrue(all(call.kwargs["input"]["tool_call_count"] == 0 for call in graph.ainvoke.await_args_list))
        self.assertTrue(all(call.kwargs["input"]["response_status"] == "pending" for call in graph.ainvoke.await_args_list))

    def test_blocked_response_never_reaches_memory(self):
        with (
            patch.object(nodes, "get_observability_manager", return_value=_Observability()),
            patch.object(nodes, "get_memory_instance") as get_memory,
        ):
            asyncio.run(nodes.memory_post_hook({"messages": [], "response_status": "blocked"}, {}))
        get_memory.assert_not_called()

    def test_sse_emits_one_complete_chunk_only_after_approved_turn(self):
        async def collect():
            return [event async for event in stream_response("hello", conversation_id="session-1", actor_id="actor-1")]

        with (
            patch("src.infrastructure.streaming.get_observability_manager", return_value=_Observability()),
            patch("src.infrastructure.streaming.apply_input_guardrail", return_value=GuardrailResult(True, "hello", "NONE")),
            patch("src.infrastructure.streaming.run_orchestrator_turn", new=AsyncMock(return_value=orchestrator_streaming.TurnResult("Approved complete answer."))) as run_turn,
        ):
            events = asyncio.run(collect())
        payloads = [json.loads(event.removeprefix("data: ").strip()) for event in events]
        self.assertEqual(payloads, [{"chunk": "Approved complete answer."}, {"done": True}])
        run_turn.assert_awaited_once()

    def test_guardrail_failure_emits_no_partial_answer_and_completes(self):
        async def collect():
            return [event async for event in stream_response("hello", conversation_id="session-1", actor_id="actor-1")]

        with (
            patch("src.infrastructure.streaming.get_observability_manager", return_value=_Observability()),
            patch("src.infrastructure.streaming.apply_input_guardrail", side_effect=GuardrailUnavailableError()),
            patch("src.infrastructure.streaming.run_orchestrator_turn", new=AsyncMock()) as run_turn,
        ):
            events = asyncio.run(collect())
        payloads = [json.loads(event.removeprefix("data: ").strip()) for event in events]
        self.assertEqual(len(payloads), 2)
        self.assertIn("error", payloads[0])
        self.assertEqual(payloads[1], {"done": True})
        run_turn.assert_not_awaited()

    def test_result_shortfall_respects_requested_count(self):
        self.assertEqual(tools._requested_result_count("Find 2 restaurants in Penang", 5), 2)
        self.assertEqual(tools._requested_result_count("Show me three restaurants", 5), 3)
        self.assertEqual(tools._requested_result_count("Find 5-star restaurants", 2), 2)


class BrowserIsolationTests(unittest.TestCase):
    def test_each_browser_operation_owns_a_toolkit_and_unique_session(self):
        toolkit_a = SimpleNamespace(get_tools_by_name=lambda: {"navigate_browser": "a"}, cleanup=AsyncMock())
        toolkit_b = SimpleNamespace(get_tools_by_name=lambda: {"navigate_browser": "b"}, cleanup=AsyncMock())
        parent = {"configurable": {"thread_id": "conversation-1", "actor_id": "actor-1"}, "tags": ["trace"]}
        with patch.object(browser, "create_browser_toolkit", side_effect=[(toolkit_a, []), (toolkit_b, [])]):
            first = browser.create_browser_operation(parent)
            second = browser.create_browser_operation(parent)

        self.assertIsNot(first[0], second[0])
        self.assertNotEqual(first[2]["configurable"]["thread_id"], second[2]["configurable"]["thread_id"])
        self.assertEqual(first[2]["configurable"]["conversation_id"], "conversation-1")
        self.assertEqual(first[2]["configurable"]["actor_id"], "actor-1")
        self.assertEqual(first[2]["tags"], ["trace"])

        async def close_both():
            await browser.close_browser_operation(first[0])
            await browser.close_browser_operation(second[0])

        asyncio.run(close_both())
        toolkit_a.cleanup.assert_awaited_once()
        toolkit_b.cleanup.assert_awaited_once()

    def test_owned_toolkit_is_cleaned_even_when_search_fails(self):
        toolkit = SimpleNamespace()
        config = {"configurable": {"thread_id": "browser-op-1"}}

        async def run():
            with (
                patch("src.application.orchestrator.workflow.agents.restaurant_explorer_agent.create_browser_operation", return_value=(toolkit, {}, config)),
                patch("src.application.orchestrator.workflow.agents.restaurant_explorer_agent.search_web", side_effect=RuntimeError("private provider detail")),
                patch("src.application.orchestrator.workflow.agents.restaurant_explorer_agent.close_browser_operation", new=AsyncMock()) as cleanup,
            ):
                result = await __import__(
                    "src.application.orchestrator.workflow.agents.restaurant_explorer_agent",
                    fromlist=["run_restaurant_explorer"],
                ).run_restaurant_explorer("restaurants")
            cleanup.assert_awaited_once_with(toolkit)
            return result

        result = asyncio.run(run())
        self.assertEqual(result.status, "error")
        self.assertNotIn("private provider detail", result.notes)

    def test_concurrent_explorer_runs_use_distinct_sessions_and_cleanup_each_owner(self):
        from src.application.orchestrator.workflow.agents import restaurant_explorer_agent as explorer

        toolkit_a = SimpleNamespace()
        toolkit_b = SimpleNamespace()
        tools_a = {"marker": object()}
        tools_b = {"marker": object()}
        config_a = {"configurable": {"thread_id": "browser-a"}}
        config_b = {"configurable": {"thread_id": "browser-b"}}
        seen = []
        both_started = asyncio.Event()

        async def fake_search(_query, operation_tools, operation_config):
            seen.append((operation_tools, operation_config["configurable"]["thread_id"]))
            if len(seen) == 2:
                both_started.set()
            await asyncio.wait_for(both_started.wait(), timeout=2)
            return "page text"

        async def fake_extract(_text, _query):
            return '[{"name":"Concurrent Result"}]'

        async def run_both():
            with (
                patch.object(explorer, "create_browser_operation", side_effect=[
                    (toolkit_a, tools_a, config_a), (toolkit_b, tools_b, config_b)
                ]),
                patch.object(explorer, "search_web", side_effect=fake_search),
                patch.object(explorer, "extract_restaurants_from_text", side_effect=fake_extract),
                patch.object(explorer, "close_browser_operation", new=AsyncMock()) as cleanup,
            ):
                results = await asyncio.gather(
                    explorer.run_restaurant_explorer("Thai food", {"configurable": {"thread_id": "conversation-1"}}),
                    explorer.run_restaurant_explorer("Sushi", {"configurable": {"thread_id": "conversation-1"}}),
                )
            cleanup.assert_has_awaits([unittest.mock.call(toolkit_a), unittest.mock.call(toolkit_b)], any_order=True)
            return results

        results = asyncio.run(run_both())
        self.assertEqual(len(seen), 2)
        self.assertEqual({entry[1] for entry in seen}, {"browser-a", "browser-b"})
        self.assertEqual({id(entry[0]) for entry in seen}, {id(tools_a), id(tools_b)})
        self.assertTrue(all(result.total_results == 1 for result in results))

    def test_cancellation_still_cleans_up_owned_browser_toolkit(self):
        from src.application.orchestrator.workflow.agents import restaurant_explorer_agent as explorer

        toolkit = SimpleNamespace()
        operation_config = {"configurable": {"thread_id": "browser-cancel"}}
        started = asyncio.Event()

        async def blocked_search(*_args):
            started.set()
            await asyncio.Event().wait()

        async def run_and_cancel():
            with (
                patch.object(explorer, "create_browser_operation", return_value=(toolkit, {}, operation_config)),
                patch.object(explorer, "search_web", side_effect=blocked_search),
                patch.object(explorer, "close_browser_operation", new=AsyncMock()) as cleanup,
            ):
                task = asyncio.create_task(explorer.run_restaurant_explorer("restaurants"))
                await asyncio.wait_for(started.wait(), timeout=2)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
                cleanup.assert_awaited_once_with(toolkit)

        asyncio.run(run_and_cancel())


class ResearchSafetyTests(unittest.TestCase):
    def test_extraction_provider_exception_is_sanitized(self):
        from src.application.orchestrator.workflow.agents import restaurant_research_agent as research

        model = SimpleNamespace(
            ainvoke=AsyncMock(side_effect=RuntimeError("sensitive provider response"))
        )
        with patch.object(research, "get_model", return_value=model):
            result = asyncio.run(
                research.extract_research_from_text("web text", "Restaurant", "Penang")
            )
        self.assertEqual(result["error_code"], "extraction_failed")
        self.assertNotIn("sensitive provider response", json.dumps(result))


class DeploymentPathTests(unittest.TestCase):
    def test_fresh_ecr_build_syncs_prompts_and_fails_on_ecr_lookup_errors(self):
        repo_root = Path(__file__).resolve().parents[2]
        workflow = (repo_root / ".github" / "workflows" / "deploy-infra.yml").read_text(encoding="utf-8")
        dockerfile = (repo_root / "restaurant-finder-api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn('set -euo pipefail', workflow)
        self.assertIn("aws ecr describe-repositories", workflow)
        self.assertNotIn('2>/dev/null || echo "0"', workflow)
        self.assertIn('python-version: "3.11"', workflow)
        self.assertIn("uv sync --locked --extra local-aws", workflow)
        self.assertIn("src.deployment.sync_prompts", workflow)
        self.assertLess(workflow.index("Sync and validate prompt manifest"), workflow.index("Build and push initial image"))
        self.assertIn("REQUIRE_PROMPT_MANIFEST=1", dockerfile)
        self.assertIn("python -m src.deployment.validate_prompts", dockerfile)

    def test_two_results_for_two_requested_does_not_need_browser_merge(self):
        primary = RestaurantSearchResult(
            query="two restaurants",
            total_results=2,
            restaurants=[parse_restaurant({"name": "A"}), parse_restaurant({"name": "B"})],
            status="success",
        )
        fallback = RestaurantSearchResult(query="two restaurants", total_results=0, restaurants=[], status="empty")
        merged = tools._merge_search_results(primary, fallback, requested_count=2)
        self.assertEqual(merged.total_results, 2)
        self.assertEqual(merged.status, "success")

    def test_primary_search_only_uses_browser_when_requested_count_is_unmet(self):
        async def run_case(query, primary_count, browser_result):
            primary = RestaurantSearchResult(
                query=query,
                total_results=primary_count,
                restaurants=[parse_restaurant({"name": f"Primary {index}"}) for index in range(primary_count)],
                status="success" if primary_count else "empty",
            )
            config = {"configurable": {"thread_id": "conversation-1"}}
            with (
                patch.object(tools.settings, "ENABLE_BROWSER_TOOLS", True),
                patch.object(tools, "run_restaurant_data_agent", new=AsyncMock(return_value=primary)),
                patch.object(tools, "run_restaurant_explorer", new=AsyncMock(return_value=browser_result)) as browser_search,
            ):
                raw = await tools.restaurant_data_tool.ainvoke(
                    {"query": query, "limit": 5},
                    config=config,
                )
            return json.loads(raw), browser_search

        not_needed = RestaurantSearchResult(query="Find 2 restaurants in Penang", total_results=0, restaurants=[], status="empty")
        requested_two, browser_search = asyncio.run(run_case("Find 2 restaurants in Penang", 2, not_needed))
        browser_search.assert_not_awaited()
        self.assertEqual(requested_two["total_results"], 2)

        one_fallback = RestaurantSearchResult(
            query="Find 4 restaurants in Penang",
            total_results=1,
            restaurants=[parse_restaurant({"name": "Browser Result"})],
            status="success",
            data_source="browser",
        )
        requested_four, browser_search = asyncio.run(run_case("Find 4 restaurants in Penang", 3, one_fallback))
        browser_search.assert_awaited_once()
        self.assertEqual(browser_search.await_args.kwargs["parent_config"]["configurable"]["thread_id"], "conversation-1")
        self.assertEqual(requested_four["total_results"], 4)
        self.assertEqual(requested_four["status"], "success")


class PackageImportTests(unittest.TestCase):
    def test_supported_imports_do_not_create_aws_clients_or_cycle(self):
        api_root = Path(__file__).resolve().parents[1]
        script = """
import boto3
def forbidden_client(*args, **kwargs):
    raise AssertionError('AWS client created during import')
boto3.client = forbidden_client
import src.domain.models
import src.domain.prompts
import src.application.orchestrator.workflow.state
import src.application.orchestrator.workflow.nodes
import src.infrastructure.api
"""
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PROMPT_SYNC_MODE"] = "false"
        env["REQUIRE_PROMPT_MANIFEST"] = "false"
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=api_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=45,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
