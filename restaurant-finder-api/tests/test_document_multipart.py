import asyncio
import copy
import io
import json
import threading
import unittest
from contextlib import contextmanager, redirect_stdout
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver

from src.application.document_rag import multipart as pure, multipart_workflow as execution, workflow
from src.application.document_rag.retrieval import resolve_query
from src.application.orchestrator import streaming
from src.application.orchestrator.workflow import graph, nodes
from src.config import settings
from src.domain.document_multipart import MultipartPlanDraft, MultipartResult, MultipartTaskResult
from src.domain.document_rag import EvidenceIntegrityError, RagCoverage, RagOutcome, RetrievedEvidence, validate_approved_document_payload
from src.evaluation import document_multipart as evaluation
from src.evaluation.rag_offline import NoTelemetry, SimulatedVectors, cloud_clients_forbidden
from src.infrastructure.guardrails import GuardrailResult
from src.infrastructure.jev_router import JevClassification

H, S = "demo-harbor-pasta", "demo-sakura-table"


class MultipartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = evaluation.load_dataset()
        cls.grounded = evaluation.compile_dataset(cls.dataset)

    def setUp(self):
        self.case = self.dataset.cases[0]
        self.manifest = self.grounded[self.case.id][0]

    @contextmanager
    def offline(self):
        with cloud_clients_forbidden(), patch("src.infrastructure.rag_observability.get_observability_manager", return_value=NoTelemetry()):
            yield

    def run_case(self, case_id="M01"):
        case = next(c for c in self.dataset.cases if c.id == case_id)
        harness = evaluation.MultipartHarness(self.grounded[case_id][0], case.simulation)
        with self.offline():
            outcome = asyncio.run(harness.run(case.question))
        return outcome, harness

    def test_five_forms_and_canonical_tasks(self):
        for case_id in ("M01", "M02", "M03", "M04", "M05", "M06"):
            case = next(c for c in self.dataset.cases if c.id == case_id)
            request = pure.compile_multipart_request(case.question, self.manifest)
            self.assertIsNotNone(request)
            self.assertEqual([(t.restaurant_id, t.criterion) for t in request.tasks], [(t.restaurant_id, t.criterion) for t in case.expected.tasks])
        request = pure.compile_multipart_request("What is the mushroom pasta price at Harbor, and what is its cancellation policy?", self.manifest)
        self.assertEqual([t.restaurant_id for t in request.tasks], [H, H])
        self.assertTrue(pure.is_multipart_candidate(self.case.question))
        self.assertFalse(pure.is_multipart_candidate("Compare mushroom pasta prices at Harbor and Sakura."))
        self.assertFalse(pure.is_multipart_candidate("What is Harbor's cancellation policy?"))
        self.assertFalse(pure.is_multipart_candidate("According to Harbor Pasta Lab's menu and policy, what is the mushroom pasta price and cancellation fee?"))
        self.assertFalse(pure.is_multipart_candidate("Compare mushroom pasta prices and cancellation policy at Harbor and Sakura."))

    def test_rejected_whole_requests_have_no_provider_calls(self):
        for number in range(14, 21):
            outcome, harness = self.run_case(f"M{number:02}")
            self.assertEqual(outcome.status, "clarify")
            self.assertEqual(sum(harness.counts().model_dump().values()), 0)
        for item in ("vegan mushroom pasta", "mushroom pasta under RM50", "mushroom pasta with no nuts", "Harbor mushroom pasta"):
            self.assertIsNone(pure.compile_multipart_request(self.case.question.replace("mushroom pasta", item), self.manifest))
        self.assertIsNone(pure.compile_multipart_request(self.case.question + "\x00", self.manifest))
        self.assertIsNone(pure.compile_multipart_request(self.case.question.replace("Sakura", "Harbor"), self.manifest))

    def test_bad_plans_never_reach_retrieval(self):
        for number in range(21, 28):
            outcome, harness = self.run_case(f"M{number:02}")
            self.assertEqual(outcome.status, "unavailable" if number == 27 else "invalid_answer")
            self.assertEqual(harness.counts().embedding, 0)
            self.assertEqual(harness.counts().selector, 0)
            self.assertEqual(harness.planner_calls, 1)
        request = pure.compile_multipart_request(self.case.question, self.manifest)
        draft = copy.deepcopy(self.case.simulation.planner)
        draft["tasks"].reverse()
        plan = pure.validate_multipart_plan(request, draft, self.manifest)
        self.assertEqual(plan.tasks, request.tasks)

    def test_strict_models_reject_forged_scope_and_fields(self):
        request = pure.compile_multipart_request(self.case.question, self.manifest)
        for changes in ({"tasks": request.tasks[:-1]+(request.tasks[0],)}, {"extra": "url"}, {"tasks": list(request.tasks)}):
            with self.assertRaises(ValueError):
                type(request).model_validate({**request.model_dump(), **changes})
        for draft in ({"tasks": [{"restaurant_id": H, "criterion": "cancellation_policy", "item": "pasta"}]*2},
                      {"tasks": [{"restaurant_id": 1, "criterion": "cancellation_policy", "item": None}]*2}):
            with self.assertRaises(ValueError):
                MultipartPlanDraft.model_validate(draft)

    def test_all_supported_records_and_four_sources(self):
        outcome, harness = self.run_case()
        self.assertEqual(outcome.status, "answered")
        self.assertEqual((outcome.coverage.supported, outcome.coverage.required), (4, 4))
        self.assertEqual([c.label for c in outcome.citations], [f"Source {i}" for i in range(1, 5)])
        self.assertEqual([c.format for c in outcome.citations], ["pdf", "md", "md", "md"])
        self.assertIn("Available at dinner only", outcome.text)
        self.assertIn("at least 12 hours", outcome.text)
        self.assertEqual(harness.results[0].difference, Decimal("4"))
        self.assertEqual(harness.counts().pin, 1)

    def test_partial_missing_item_has_no_price_difference(self):
        outcome, harness = self.run_case("M07")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.coverage.supported, 3)
        self.assertEqual(len(outcome.citations), 3)
        self.assertIsNone(harness.results[0].difference)
        self.assertIn("Not found in retrieved", outcome.text)

    def test_policy_failure_does_not_prevent_supported_price_calculation(self):
        outcome, harness = self.run_case("M11")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(harness.results[0].difference, Decimal("4"))
        self.assertIn("RM4 lower", outcome.text)
        self.assertEqual(len(outcome.citations), 3)

    def test_faults_reject_entire_factual_answer(self):
        for number in list(range(28, 36))+[37]:
            outcome, _ = self.run_case(f"M{number:02}")
            self.assertEqual(outcome.status, "invalid_answer", number)
            self.assertEqual(outcome.citations, [])
            self.assertIsNone(outcome.coverage)
            self.assertNotIn("RM32", outcome.text)

    def test_incompatible_units_disable_arithmetic(self):
        outcome, harness = self.run_case("M36")
        self.assertEqual(outcome.status, "answered")
        self.assertIsNone(harness.results[0].difference)
        self.assertIn("matching currency and serving units", outcome.text)

    def test_pointer_change_does_not_repin(self):
        outcome, harness = self.run_case("M38")
        self.assertEqual(harness.pin_calls, 1)
        self.assertTrue(all(c.generation_id == self.manifest.generation_id for c in outcome.citations))

    def test_two_workers_overlap_and_concurrency_never_exceeds_two(self):
        harness = evaluation.MultipartHarness(self.manifest, self.case.simulation)
        original = harness.dependencies.retriever_factory
        barrier, lock, counts = threading.Barrier(2), threading.Lock(), {"active": 0, "maximum": 0}

        def factory(rid):
            retriever = original(rid)
            retrieve = retriever.retrieve
            def wrapped(*args, **kwargs):
                with lock:
                    counts["active"] += 1
                    counts["maximum"] = max(counts["maximum"], counts["active"])
                try:
                    barrier.wait(timeout=2)
                    return retrieve(*args, **kwargs)
                finally:
                    with lock:
                        counts["active"] -= 1
            retriever.retrieve = wrapped
            return retriever
        harness.dependencies = replace(harness.dependencies, retriever_factory=factory)
        with self.offline():
            outcome = asyncio.run(harness.run(self.case.question))
        self.assertEqual(outcome.status, "answered")
        self.assertEqual(counts, {"active": 0, "maximum": 2})

    def test_actual_timeout_stops_threads_before_subsequent_provider_operations(self):
        import time
        harness = evaluation.MultipartHarness(self.manifest, self.case.simulation)
        original = harness.dependencies.retriever_factory
        released, started = threading.Event(), threading.Event()
        clients = []
        def factory(rid):
            value = original(rid)
            retrieve = value.retrieve
            fake_client = Mock()
            # The normal harness shares only a fake data store. Here clients
            # must belong to separate adapters as they do in the real factory.
            value.store = copy.copy(value.store)
            value.store._client = fake_client
            clients.append(fake_client)
            def wrapped(*args, **kwargs):
                started.set()
                if not released.wait(timeout=1):
                    raise AssertionError("Offline timeout release failed")
                return retrieve(*args, **kwargs)
            value.retrieve = wrapped
            return value
        harness.dependencies = replace(harness.dependencies, retriever_factory=factory)
        async def run():
            with patch.object(settings, "DOCUMENT_RAG_ENABLED", True), patch.object(settings, "DOCUMENT_MULTIPART_ENABLED", True):
                operation = asyncio.create_task(execution.answer_multipart(self.case.question, {}, dependencies=harness.dependencies,
                    deadline=time.monotonic()+2.15))
                await asyncio.to_thread(started.wait, 1)
                outcome = await operation
                released.set()
                return outcome
        try:
            with self.offline():
                outcome = asyncio.run(run())
        finally:
            released.set()
        self.assertEqual(outcome.status, "unavailable")
        self.assertEqual(outcome.retrieval_count, 2)
        self.assertEqual(harness.counts().embedding, 0)
        self.assertEqual(harness.counts().selector, 0)
        self.assertEqual(len(clients), 2)
        for client in clients:
            client.close.assert_called_once()

    def test_trace_attributes_contain_counts_and_fixed_reasons_without_payload(self):
        entries = []
        class Telemetry(NoTelemetry):
            @contextmanager
            def create_span(self, name, attributes=None):
                fields = dict(attributes or {})
                entries.append((name, fields))
                yield SimpleNamespace(set_attribute=lambda key, value: fields.update({key: value}))
        case = next(c for c in self.dataset.cases if c.id == "M11")
        harness = evaluation.MultipartHarness(self.manifest, case.simulation)
        with cloud_clients_forbidden(), patch("src.infrastructure.rag_observability.get_observability_manager", return_value=Telemetry()):
            outcome = asyncio.run(harness.run(case.question))
        self.assertEqual(outcome.status, "partial")
        aggregate = next(fields for name, fields in entries if name == "rag.multipart.aggregate")
        self.assertEqual((aggregate["rag.required"], aggregate["rag.supported"]), (4, 3))
        complete = [fields for name, fields in entries if name == "rag.multipart.worker.complete"]
        self.assertEqual(len(complete), 4)
        self.assertTrue(any(f["rag.reason"] == "provider_error" for f in complete))
        self.assertNotIn("SIMULATED_PRIVATE", str(entries))
        self.assertNotIn("mushroom pasta", str(entries))

    def test_shared_deadline_keeps_completed_rows_and_stops_queued_operations(self):
        for _ in range(3):
            outcome, harness = self.run_case("M13")
            self.assertEqual(outcome.status, "partial")
            self.assertEqual([t.status for t in outcome.coverage.tasks], ["supported", "supported", "unavailable", "unavailable"])
            self.assertEqual((harness.counts().embedding, harness.counts().retrieval, harness.counts().selector), (2, 2, 2))
        with self.offline(), patch.object(settings, "DOCUMENT_RAG_ENABLED", True), patch.object(settings, "DOCUMENT_MULTIPART_ENABLED", True):
            harness = evaluation.MultipartHarness(self.manifest, self.case.simulation)
            outcome = asyncio.run(execution.answer_multipart(self.case.question, {}, dependencies=harness.dependencies, deadline=0, clock=lambda: 0))
            self.assertEqual(outcome.status, "unavailable")
            self.assertEqual(harness.pin_calls, 0)

    def test_no_evidence_or_provider_failure_accounts_for_every_task(self):
        for case_id, status in (("M09", "insufficient_evidence"), ("M10", "unavailable"), ("M12", "unavailable")):
            outcome, harness = self.run_case(case_id)
            self.assertEqual(outcome.status, status)
            self.assertEqual(len(harness.results[0].rows), 4)
            self.assertEqual(harness.counts().selector, 0)
            self.assertEqual(outcome.citations, [])

    def test_disabled_gates_make_no_calls(self):
        outcome, harness = self.run_case("M39")
        self.assertEqual(outcome.status, "disabled")
        self.assertEqual(sum(harness.counts().model_dump().values()), 0)
        harness.simulation = harness.simulation.model_copy(update={"multipart_enabled": True, "rag_enabled": False})
        with self.offline():
            self.assertEqual(asyncio.run(harness.run(self.case.question)).status, "disabled")
        self.assertEqual(harness.planner_calls, 0)

    def test_coverage_and_mode_caps_cannot_be_forged(self):
        outcome, _ = self.run_case()
        for changes in ({"mode": "single"}, {"coverage": None}, {"status": "partial"}, {"restaurant_id": H}):
            with self.assertRaises(ValueError):
                RagOutcome.model_validate({**outcome.model_dump(), **changes})
        coverage = outcome.coverage.model_dump()
        for changes in ({"supported": 3}, {"required": 3}, {"tasks": coverage["tasks"][:-1]}, {"supported": True}):
            with self.assertRaises(ValueError):
                RagCoverage.model_validate({**coverage, **changes})
        malformed = copy.deepcopy(coverage)
        malformed["tasks"][3]["source_label"] = "Source 3"
        with self.assertRaises(ValueError):
            RagCoverage.model_validate(malformed)
        with self.assertRaises(ValueError):
            validate_approved_document_payload("comparison", "answered", outcome.generation_id, outcome.citations[:3])

    def test_aggregation_rejects_missing_duplicate_and_changed_rows(self):
        _, harness = self.run_case()
        result = harness.results[0]
        for rows in (result.rows[:-1], result.rows[:-1]+(result.rows[0],)):
            with self.assertRaises(ValueError):
                pure.aggregate_multipart(result.plan, rows, self.manifest)
        for changes in ({"supported": 3}, {"difference": Decimal("99")}, {"citations": ()}):
            with self.assertRaises(ValueError):
                MultipartResult.model_validate({**result.model_dump(), **changes})
        with self.assertRaises(ValueError):
            MultipartTaskResult(task=result.plan.tasks[1], status="supported", reason="unsupported_price_format",
                retrieval_started=True, selection=result.rows[1].selection, evidence=result.rows[1].evidence)

    def test_policy_long_split_and_missing_layouts_are_not_truncated(self):
        from src.application.document_rag.ingestion import prepare_generation
        from src.infrastructure.document_parser import load_corpus
        corpus, originals = load_corpus(evaluation.API_ROOT/"sample_documents/corpus-v2.json")
        task = pure.compile_multipart_request(self.case.question, self.manifest).tasks[1]
        for body in ("A cancellation condition. "*30, ("A condition. "*100)+"\n\n"+("A later condition. "*80)):
            with TemporaryDirectory() as directory:
                root = Path(directory)
                for spec in corpus.documents:
                    (root/spec.path).write_bytes(originals[spec.document_id])
                (root/"harbor-policy.md").write_text("# Fictional policy\n\n## Reservations and cancellation\n\n"+body+"\n", encoding="utf-8")
                (root/"corpus.json").write_text(corpus.model_dump_json(), encoding="utf-8")
                manifest, _ = prepare_generation(root/"corpus.json")
                evidence = [RetrievedEvidence(**c.model_dump(exclude={"key"}), generation_id=manifest.generation_id, distance=.1,
                                             restaurant_name=task.restaurant_name) for c in manifest.chunks if c.restaurant_id == H and c.document_type == "policy"]
                self.assertEqual(pure.policy_record(task, evidence, manifest), (None, "unsupported_policy_layout"))
        self.assertEqual(pure.policy_record(task, [], self.manifest), (None, "missing_evidence"))

    def test_pinned_catalog_disagreement_prevents_planner(self):
        harness = evaluation.MultipartHarness(self.manifest.model_copy(update={"restaurants": self.manifest.restaurants[1:]}), self.case.simulation)
        with self.offline():
            outcome = asyncio.run(harness.run(self.case.question))
        self.assertEqual(outcome.status, "invalid_answer")
        self.assertEqual(harness.planner_calls, 0)

    def test_owned_model_call_limits_tokens_and_closes_clients(self):
        calls, client = [], Mock()
        model = SimpleNamespace(client=client, bedrock_client=client)
        def model_copy(update):
            calls.append(update)
            return model
        model.model_copy = model_copy
        model.with_structured_output = lambda schema: RunnableLambda(lambda data: {"schema": schema.__name__})
        prompt = SimpleNamespace(prompt="Only return tasks")
        with self.offline(), patch("src.infrastructure.model.get_model", return_value=model) as factory:
            value = execution.OwnedStructuredCall(prompt, MultipartPlanDraft, 1000, execution.PLANNER_CONFIG)
            result = asyncio.run(value.ainvoke({"payload": "untrusted"}, {}))
        self.assertEqual(result, {"schema": "MultipartPlanDraft"})
        self.assertEqual(calls, [{"max_tokens": 1000}])
        self.assertEqual(factory.call_args.kwargs["client_config"].retries["total_max_attempts"], 1)
        self.assertEqual(factory.call_args.kwargs["temperature"], 0)
        client.close.assert_called_once()

    def test_model_operation_stopped_before_creation(self):
        call = execution.OwnedStructuredCall(SimpleNamespace(prompt="tasks"), MultipartPlanDraft, 1000, execution.PLANNER_CONFIG)
        call.stopped.set()
        with patch("src.infrastructure.model.get_model", side_effect=AssertionError("must not construct")) as factory:
            with self.assertRaises(TimeoutError):
                asyncio.run(call.ainvoke({"payload": "x"}, {}))
        factory.assert_not_called()

    def test_mask_block_and_partial_approval_release_only_matching_sources(self):
        outcome, _ = self.run_case("M07")
        state = {"messages": [HumanMessage(content=self.case.question), AIMessage(content=outcome.text)], "intent": "document_qa",
                 "rag_mode": "multipart", "rag_status": outcome.status, "rag_generation": outcome.generation_id,
                 "rag_pending_citations": [c.model_dump() for c in outcome.citations], "rag_pending_coverage": outcome.coverage.model_dump(),
                 "rag_approved_scope": H}
        for allowed, text in ((True, outcome.text), (True, "masked"), (False, "")):
            with self.offline(), patch.object(nodes, "apply_output_guardrail", return_value=GuardrailResult(allowed, text, "NONE")):
                result = asyncio.run(nodes.output_guardrail_node(state, {}))
            self.assertEqual(len(result["rag_approved_citations"]), 3 if allowed and text == outcome.text else 0)
            self.assertEqual(result["rag_approved_coverage"] is not None, allowed and text == outcome.text)
            self.assertIsNone(result["rag_pending_coverage"])
            self.assertEqual("rag_approved_scope" in result, allowed)
        for changes in ({"rag_pending_coverage": None}, {"rag_pending_citations": []}):
            with self.offline(), patch.object(nodes, "apply_output_guardrail", return_value=GuardrailResult(True, outcome.text, "NONE")):
                with self.assertRaises(ValueError):
                    asyncio.run(nodes.output_guardrail_node({**state, **changes}, {}))

    def test_parent_graph_one_guardrail_memory_save_and_private_checkpoint(self):
        harness = evaluation.MultipartHarness(self.manifest, self.case.simulation)
        saver, memory = InMemorySaver(), SimpleNamespace(process_turn=Mock(return_value={"success": True}))
        guard = Mock(side_effect=lambda text: GuardrailResult(True, text, "NONE"))

        async def run():
            compiled = graph.create_orchestrator_graph(force_recreate=True)
            config = {"configurable": {"thread_id": "multipart-offline", "actor_id": "demo"}}
            result = await compiled.ainvoke({"messages": [HumanMessage(content=self.case.question)], "rag_approved_scope": H}, config)
            self.assertEqual(len(result["messages"]), 2)
            self.assertEqual(len(result["rag_approved_citations"]), 4)
            self.assertEqual(result["rag_approved_coverage"]["supported"], 4)
            self.assertIsNone(result["rag_approved_scope"])
            self.assertTrue({"manifest", "plan", "rows", "result", "ledger"}.isdisjoint(compiled.get_state(config).values))
            self.assertNotIn("chunk_id", str(result["messages"][-1].additional_kwargs))
            guard.assert_called_once()
            memory.process_turn.assert_called_once()
            self.assertEqual(memory.process_turn.call_args.kwargs["agent_response"], result["messages"][-1].content)
            self.assertIsNotNone(resolve_query("What about its parking policy?", self.manifest, result["rag_approved_scope"]).clarification)
            self.assertEqual(resolve_query("What is Harbor's parking policy?", self.manifest).restaurant_id, H)

        with self.offline(), patch.object(settings, "DOCUMENT_RAG_ENABLED", True), patch.object(settings, "DOCUMENT_MULTIPART_ENABLED", True),\
             patch.object(graph, "_graph_instance", None), patch.object(graph, "get_orchestrator_tools", return_value=[]),\
             patch.object(graph, "ShortTermMemory", return_value=SimpleNamespace(get_memory=lambda: saver)),\
             patch.object(nodes, "classify_with_jev", return_value=JevClassification("document_qa", .9)),\
             patch.object(nodes, "apply_output_guardrail", guard), patch.object(nodes, "get_memory_instance", return_value=memory),\
             patch.object(execution, "MultipartDependencies", return_value=harness.dependencies):
            asyncio.run(run())

    def test_turn_extracts_four_sources_and_resets_transient_coverage(self):
        outcome, _ = self.run_case()
        response = {"messages": [HumanMessage(content="q"), AIMessage(content=outcome.text)], "response_status": "approved",
                    "rag_mode": "multipart", "rag_status": "answered", "rag_generation": outcome.generation_id,
                    "rag_approved_citations": [c.model_dump() for c in outcome.citations], "rag_approved_coverage": outcome.coverage.model_dump()}
        fake = SimpleNamespace(ainvoke=AsyncMock(return_value=response))
        with patch.object(streaming, "create_orchestrator_graph", return_value=fake):
            result = asyncio.run(streaming.run_orchestrator_turn("hello", conversation_id="multipart-turn"))
        self.assertEqual(len(result.citations), 4)
        data = fake.ainvoke.await_args.kwargs["input"]
        self.assertIsNone(data["rag_pending_coverage"])
        self.assertIsNone(data["rag_approved_coverage"])
        response["rag_approved_coverage"] = None
        with patch.object(streaming, "create_orchestrator_graph", return_value=fake), self.assertRaises(ValueError):
            asyncio.run(streaming.run_orchestrator_turn("hello", conversation_id="multipart-turn"))


class MultipartEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = evaluation.load_dataset()
        cls.grounded = evaluation.compile_dataset(cls.dataset)
        cls.observations = evaluation.run_offline(cls.dataset, cls.grounded)

    def test_all_40_independent_cases_and_missing_observation(self):
        report = evaluation.evaluate(self.dataset, self.observations, self.grounded)
        self.assertTrue(report["passed"], report["failed_case_ids"])
        self.assertEqual(report["observed_cases"], 40)
        self.assertFalse(evaluation.evaluate(self.dataset, self.observations[:-1], self.grounded)["passed"])

    def test_scorer_rejects_forged_text_tasks_coverage_math_and_sources(self):
        for changes in ({"text": "SECRET_ANSWER"}, {"text": self.observations[0]["text"]+"\nUnfounded new fact."},
                        {"rows": []}, {"coverage": None}, {"difference": "999"}, {"citations": []}, {"evidence": []}):
            altered = [{**self.observations[0], **changes}, *self.observations[1:]]
            self.assertFalse(evaluation.evaluate(self.dataset, altered, self.grounded)["passed"])
        with self.assertRaises(ValueError):
            evaluation.evaluate(self.dataset, self.observations+[self.observations[0]], self.grounded)

    def test_dataset_validates_gold_and_rejects_duplicate_cases(self):
        data = self.dataset.model_dump()
        data["cases"][0]["expected"]["tasks"][0]["restaurant_id"] = "demo-unknown"
        with self.assertRaises(ValueError):
            evaluation.compile_dataset(evaluation.Dataset.model_validate(data))
        data = self.dataset.model_dump()
        data["cases"][1]["id"] = "M01"
        with self.assertRaises(ValueError):
            evaluation.Dataset.model_validate(data)

    def test_cli_reports_pass_failure_invalid_input_and_no_private_payload(self):
        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            path = Path(directory)/"report.json"
            self.assertEqual(evaluation.main(["--offline", "--output", str(path)]), 0)
            self.assertIn("simulated", path.with_suffix(".md").read_text())
            self.assertNotIn("SIMULATED_PRIVATE", path.read_text())
            with patch.object(evaluation, "evaluate", return_value={**evaluation.evaluate(self.dataset, self.observations, self.grounded), "passed": False}):
                self.assertEqual(evaluation.main(["--offline", "--output", str(path)]), 1)
            self.assertEqual(evaluation.main(["--offline", "--dataset", str(Path(directory)/"missing.json")]), 2)


if __name__ == "__main__":
    unittest.main()
