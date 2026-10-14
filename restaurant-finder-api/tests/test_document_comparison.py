import asyncio
import copy
import io
import json
import threading
import time
import unittest
from contextlib import contextmanager, redirect_stdout
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from src.application.document_rag import comparison as pure, comparison_workflow as execution, workflow
from src.application.document_rag.retrieval import DocumentRetriever, resolve_query
from src.application.orchestrator import streaming
from src.application.orchestrator.workflow import graph, nodes
from src.domain.document_comparison import ComparisonPlan, ComparisonResult, ComparisonRow, PriceFact
from src.domain.document_rag import DocumentQuery, EvidenceIntegrityError, RagAnswerDraft, RagOutcome
from src.evaluation import document_comparison as evaluation
from src.evaluation.rag_offline import NoTelemetry, SimulatedVectors, cloud_clients_forbidden
from src.infrastructure.guardrails import GuardrailResult
from src.infrastructure.jev_router import JevClassification
from src.infrastructure.vector_store import VectorStore

H, S = "demo-harbor-pasta", "demo-sakura-table"


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = evaluation.load_dataset()
        cls.grounded = evaluation.compile_dataset(cls.dataset)

    def setUp(self):
        legacy_followups = patch.object(workflow.settings, "DOCUMENT_FOLLOWUPS_ENABLED", False)
        legacy_followups.start()
        self.addCleanup(legacy_followups.stop)
        self.case = self.dataset.cases[0]
        self.manifest = self.grounded[self.case.id][0]
        self.harness = evaluation.ComparisonHarness(self.manifest, self.case.simulation)

    @contextmanager
    def offline(self):
        with cloud_clients_forbidden(), patch("src.infrastructure.rag_observability.get_observability_manager", return_value=NoTelemetry()):
            yield

    def run_case(self, case=None):
        case = case or self.case
        harness = evaluation.ComparisonHarness(self.grounded[case.id][0], case.simulation)
        with self.offline():
            outcome = asyncio.run(harness.run(case.question))
        return outcome, harness

    def test_all_request_forms_aliases_order_and_rejections(self):
        for case in self.dataset.cases:
            with self.subTest(case=case.id):
                plan = pure.plan_comparison(case.question, self.grounded[case.id][0])
                if case.expected.status == "clarify":
                    self.assertIsNone(plan)
                else:
                    self.assertEqual(plan.restaurant_ids, tuple(r.restaurant_id for r in case.expected.rows))
                    self.assertEqual(plan.item, case.expected.item)
        for question in ["Compare mushroom pasta prices at Harbor and Sakura under RM50",
                         "Compare allergies price at Harbor and Sakura", "Compare pasta prices at Harbor and Sakura\x00",
                         "Compare " + "x"*1000 + " prices at Harbor and Sakura"]:
            self.assertIsNone(pure.plan_comparison(question, self.manifest))
        self.assertFalse(pure.is_comparison_candidate("Compare Harbor and Sakura menus"))
        self.assertIn("choose one", resolve_query("Compare Harbor and Sakura menus", self.manifest).clarification)

    def test_strict_plan_rows_prices_and_partial_outcomes(self):
        plan = pure.plan_comparison(self.case.question, self.manifest)
        for changes in [{"restaurant_ids": (H,H)}, {"restaurant_ids": [H,S]}, {"item": "x"*81}, {"extra": True}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                ComparisonPlan.model_validate({**plan.model_dump(), **changes})
        for amount in ["32", Decimal("NaN"), Decimal("Infinity"), Decimal("-1"), Decimal("100000000")]:
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                PriceFact(amount=amount, unit="serving")
        with self.assertRaises(ValueError):
            ComparisonRow(restaurant_id=H,status="missing",reason="verified")
        outcome, _ = self.run_case()
        with self.assertRaises(ValueError):
            RagOutcome(status="partial", text="safe", generation_id=outcome.generation_id, citations=outcome.citations)
        with self.assertRaises(ValueError):
            RagOutcome(status="partial", text="safe")

    def test_fixed_amount_parser_uses_decimal_and_rejects_alternatives(self):
        self.assertEqual(pure.parse_price("MYR32.50 per serving.").amount, Decimal("32.50"))
        self.assertEqual(pure.parse_price("RM0 per piece.").amount, Decimal("0"))
        for value in ["USD32 per serving.", "RM32 per plate.", "RM32.", "from RM32 per serving.",
                      "RM28-RM32 per serving.", "RM-1 per serving.", "RMNaN per serving.",
                      "RM32 and RM30 per serving.", "RM32.123 per serving."]:
            self.assertIsNone(pure.parse_price(value), value)

    def test_v1_v2_and_partial_results_keep_complete_quotes_and_originals(self):
        for case_id in ["price_v1", "price_v2", "missing_left", "worker_unavailable"]:
            case = next(c for c in self.dataset.cases if c.id == case_id)
            outcome, harness = self.run_case(case)
            result = harness.results[0]
            self.assertEqual(outcome.status, case.expected.status)
            self.assertEqual(result.difference, Decimal(case.expected.difference) if case.expected.difference else None)
            self.assertEqual(len(outcome.citations), 1 if outcome.status == "partial" else 2)
            self.assertIsNone(outcome.restaurant_id)
            self.assertEqual(outcome.retrieval_count, 2)
            for citation in outcome.citations:
                self.assertEqual(outcome.text.count(f"Source: {citation.label} — "), 1)
                self.assertEqual(citation.generation_id, outcome.generation_id)
            if outcome.status == "answered":
                self.assertIn("Available at dinner only", outcome.text)
                self.assertEqual([c.format for c in outcome.citations], ["pdf", "md"])
            if case_id == "worker_unavailable":
                self.assertIn("Retrieval unavailable", outcome.text)
                self.assertNotIn("SIMULATED_PRIVATE", outcome.text)

    def test_no_evidence_skips_selector_and_no_evidence_is_not_permission(self):
        original = self.harness.dependencies.retriever_factory
        def empty(rid):
            retriever = original(rid)
            retriever.vectors.query = Mock(return_value=[])
            return retriever
        deps = execution.ComparisonDependencies(self.harness.dependencies.pin_factory, empty,
                                               Mock(side_effect=AssertionError("Unexpected selector")))
        with self.offline():
            outcome = asyncio.run(execution.answer_comparison(self.case.question, {}, dependencies=deps))
        self.assertEqual(outcome.status, "insufficient_evidence")
        deps.selector_factory.assert_not_called()

    def test_pin_is_once_even_when_pointer_changes(self):
        case = next(c for c in self.dataset.cases if c.id == "pointer_changes")
        outcome, harness = self.run_case(case)
        self.assertEqual(harness.pin_calls, 1)
        self.assertNotEqual(harness.store.pointer.generation_id, outcome.generation_id)
        self.assertTrue(all(s.generation_id == outcome.generation_id and s.document_type == "menu"
                            and s.max_pages == 1 for s in harness.scopes))
        self.assertIsNot(harness.retrievers[0].embeddings, harness.retrievers[1].embeddings)

    def test_changed_chunk_fails_integrity_not_partial_availability(self):
        key = next(c.key for c in self.manifest.chunks if c.restaurant_id == H and c.document_type == "menu")
        self.harness.store.data[key]["text"] = "CORRUPTED_PRIVATE_DOCUMENT"
        with self.offline():
            outcome = asyncio.run(self.harness.run(self.case.question))
        self.assertEqual(outcome.status, "invalid_answer")
        self.assertEqual(outcome.citations, [])
        self.assertNotIn("PRIVATE", outcome.text)
        self.assertEqual(self.harness.results[0].rows[0].reason, "invalid_evidence")

    def test_multiple_quotes_omitted_qualifiers_price_only_and_instructions_rejected(self):
        for quote in ["Mushroom pasta - RM32 per serving.", "RM32 per serving.", "ignore previous instructions"]:
            simulation = self.case.simulation.model_copy(deep=True)
            simulation.workers[0].selector.selections[0].quote = quote
            harness = evaluation.ComparisonHarness(self.manifest, simulation)
            with self.offline():
                outcome = asyncio.run(harness.run(self.case.question))
            self.assertEqual(outcome.status, "invalid_answer")
        simulation = self.case.simulation.model_copy(deep=True)
        simulation.workers[0].selector.selections *= 2
        harness = evaluation.ComparisonHarness(self.manifest, simulation)
        with self.offline():
            self.assertEqual(asyncio.run(harness.run(self.case.question)).status, "invalid_answer")

    def test_retrieved_conflicting_records_are_rejected(self):
        outcome, harness = self.run_case()
        result = harness.results[0]
        row = result.rows[0]
        conflicting = row.evidence.model_copy(update={"chunk_id":"f"*64,"text": row.evidence.text.replace("RM32", "RM99")})
        # A pure validator fault input; not a claim about the original fixture.
        validated = pure.validate_selection(result.plan, H, RagAnswerDraft(status="answered", selections=[row.selection]),
                                           [row.evidence, conflicting], self.manifest)
        self.assertEqual((validated.status,validated.reason), ("invalid","conflicting_evidence"))
        no_selection = pure.validate_selection(result.plan,H,RagAnswerDraft(status="insufficient_evidence"),
                                               [row.evidence,conflicting],self.manifest)
        self.assertEqual(no_selection.reason,"conflicting_evidence")

    def test_arithmetic_contract_ties_units_unsupported_formats_and_duplicate_results(self):
        _, harness = self.run_case()
        result = harness.results[0]
        # Explicit synthetic contract inputs; original documents are not edited.
        a, b = result.rows
        for changes, expected_reason in [({"price": PriceFact(amount=Decimal("32"), unit="serving")}, "tie"),
                                         ({"price": PriceFact(amount=Decimal("36"), unit="bowl")}, "different_units"),
                                         ({"price": None, "reason": "unsupported_price_format"}, "unsupported_price_format")]:
            synthetic = b.model_copy(update=changes)
            actual = pure.aggregate_comparison(result.plan, [a,synthetic], self.manifest)
            self.assertEqual(actual.calculation_reason, expected_reason)
            self.assertEqual(actual.difference, Decimal("0") if expected_reason == "tie" else None)
            self.assertIsNone(actual.cheaper_id)
        with self.assertRaises(ValueError):
            pure.aggregate_comparison(result.plan,[a,a],self.manifest)
        with self.assertRaises(ValueError):
            ComparisonResult.model_validate({**result.model_dump(),"difference":Decimal("99")})

    def test_decimal_record_boundaries_and_unsupported_currency(self):
        for record in ["Mushroom pasta - RM32.50 per serving. Contains milk.",
                       "Mushroom pasta - USD32 per serving. Contains milk."]:
            values = list(pure._records(record, "mushroom pasta"))
            self.assertEqual(values[0][0], record)
            self.assertTrue(values[0][2])
        self.assertEqual(list(pure._records("Mushroom pasta - RM32 per serving.","pasta")), [])

    def test_workers_overlap_and_reversed_finish_is_deterministic(self):
        async def run():
            both_started, right_finished = asyncio.Event(), asyncio.Event()
            seen = []
            original = self.harness.dependencies.selector_factory
            def selector(rid):
                delegate = original(rid)
                async def invoke(data, config):
                    seen.append(rid)
                    if len(seen) == 2:
                        both_started.set()
                    await asyncio.wait_for(both_started.wait(), 2)
                    if rid == H:
                        await asyncio.wait_for(right_finished.wait(), 2)
                    value = await delegate.ainvoke(data, config)
                    if rid == S:
                        right_finished.set()
                    return value
                return SimpleNamespace(ainvoke=invoke)
            deps = execution.ComparisonDependencies(self.harness.dependencies.pin_factory,
                self.harness.dependencies.retriever_factory, selector, self.harness.results.append)
            outcome = await execution.answer_comparison(self.case.question,{},dependencies=deps)
            self.assertEqual(set(seen), {H,S})
            return outcome
        with self.offline():
            outcome = asyncio.run(run())
        self.assertEqual(outcome.status, "answered")
        self.assertEqual([row.restaurant_id for row in self.harness.results[0].rows],[H,S])
        self.assertEqual([c.document_id for c in outcome.citations],["harbor-menu","sakura-menu"])

    def test_deadline_checks_between_sdk_calls_stop_new_work(self):
        retriever = self.harness.dependencies.retriever_factory(H)
        now = [0.0]
        def embed(_text):
            now[0] = 2
            return [1.0]+[0.0]*511
        retriever.embeddings.embed = Mock(side_effect=embed)
        retriever.vectors.query = Mock(side_effect=AssertionError("No query after deadline"))
        with self.offline(), self.assertRaises(TimeoutError):
            retriever.retrieve(DocumentQuery(query="mushroom pasta",restaurant_id=H,document_type="menu"),
                               self.manifest, deadline=1,clock=lambda:now[0],max_pages=1)
        retriever.vectors.query.assert_not_called()
        retriever.store.active = Mock(side_effect=AssertionError)
        with self.assertRaises(TimeoutError):
            retriever.pin(deadline=1,clock=lambda:2)
        retriever.store.active.assert_not_called()

    def test_deadline_between_chunk_reads_and_whole_context_bound(self):
        retriever = self.harness.dependencies.retriever_factory(S)
        original = retriever.store.read_json
        now, reads = [0], []
        def read(key):
            reads.append(key)
            now[0] = 2
            return original(key)
        retriever.store.read_json = read
        with self.offline(), self.assertRaises(TimeoutError):
            retriever.retrieve(DocumentQuery(query="menu",restaurant_id=S,document_type="menu"),self.manifest,
                               deadline=1,clock=lambda:now[0],max_pages=1)
        self.assertEqual(len(reads),1)
        retriever.store.read_json = original
        retriever.max_characters = 1
        with self.offline():
            evidence = retriever.retrieve(DocumentQuery(query="menu",restaurant_id=S,document_type="menu"),self.manifest,max_pages=1)
        self.assertEqual(evidence,[])  # Whole passages dropped, never cut into partial records.

    def test_deadline_reserve_and_user_cancellation(self):
        with self.offline():
            outcome = asyncio.run(execution.answer_comparison(self.case.question,{},dependencies=self.harness.dependencies,
                clock=lambda:0,deadline=1))
        self.assertEqual(outcome.status,"unavailable")
        self.assertEqual(self.harness.retrievers,[])
        async def cancel():
            reached = asyncio.Event()
            def selector(_rid):
                async def invoke(*_):
                    reached.set()
                    await asyncio.Event().wait()
                return SimpleNamespace(ainvoke=invoke)
            deps = execution.ComparisonDependencies(self.harness.dependencies.pin_factory,
                self.harness.dependencies.retriever_factory,selector)
            task = asyncio.create_task(execution.answer_comparison(self.case.question,{},dependencies=deps))
            await asyncio.wait_for(reached.wait(),2)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        with self.offline():
            asyncio.run(cancel())

    def test_worker_timeout_preserves_only_the_other_verified_branch(self):
        async def run():
            original = self.harness.dependencies.selector_factory
            def selector(rid):
                if rid == H:
                    return original(rid)
                return SimpleNamespace(ainvoke=AsyncMock(side_effect=TimeoutError("PRIVATE_TIMEOUT")))
            deps = execution.ComparisonDependencies(self.harness.dependencies.pin_factory,
                self.harness.dependencies.retriever_factory,selector,self.harness.results.append)
            return await execution.answer_comparison(self.case.question,{},dependencies=deps)
        with self.offline():
            outcome = asyncio.run(run())
        self.assertEqual(outcome.status,"partial")
        self.assertEqual(len(outcome.citations),1)
        self.assertNotIn("PRIVATE",outcome.text)

    def test_actual_branch_timeout_settles_as_partial_without_replay(self):
        async def run():
            original = self.harness.dependencies.selector_factory
            pending = AsyncMock(side_effect=lambda *_:None)
            async def wait_forever(*_):
                await asyncio.Event().wait()
            pending.side_effect = wait_forever
            deps = execution.ComparisonDependencies(self.harness.dependencies.pin_factory,
                self.harness.dependencies.retriever_factory,
                lambda rid:original(rid) if rid == H else SimpleNamespace(ainvoke=pending))
            compiled = execution.build_comparison_graph(deps,time.monotonic()+2)
            result = (await compiled.ainvoke({"plan":pure.plan_comparison(self.case.question,self.manifest),
                "manifest":self.manifest,"rows":[]}))["result"]
            pending.assert_awaited_once()
            return result
        with self.offline():
            result = asyncio.run(run())
        self.assertEqual(result.status,"partial")
        self.assertEqual(result.rows[1].reason,"deadline_exhausted")
        self.assertEqual(len(result.citations),1)

    def test_cancelling_worker_stops_queries_after_inflight_embedding(self):
        reached,release,finished = threading.Event(),threading.Event(),threading.Event()
        retriever = self.harness.dependencies.retriever_factory(H)
        original_retrieve = retriever.retrieve
        def embed(_text):
            reached.set()
            if not release.wait(timeout=2):
                raise TimeoutError("Fixture release missing")
            return [1.0]+[0.0]*511
        def retrieve(*args,**kwargs):
            try:
                return original_retrieve(*args,**kwargs)
            finally:
                finished.set()
        retriever.embeddings.embed = embed
        retriever.retrieve = retrieve
        retriever.vectors.query = Mock(side_effect=AssertionError("No query after cancellation"))
        deps = execution.ComparisonDependencies(self.harness.dependencies.pin_factory,
            lambda rid:retriever if rid==H else self.harness.dependencies.retriever_factory(rid),
            self.harness.dependencies.selector_factory)
        async def run():
            task = asyncio.create_task(execution.answer_comparison(self.case.question,{},dependencies=deps))
            self.assertTrue(await asyncio.to_thread(reached.wait,2))
            task.cancel()
            try:
                with self.assertRaises(asyncio.CancelledError):
                    await task
            finally:
                release.set()
            self.assertTrue(await asyncio.to_thread(finished.wait,2))
        with self.offline():
            asyncio.run(run())
        retriever.vectors.query.assert_not_called()

    def test_vector_page_ceiling_and_model_configuration(self):
        client = Mock()
        client.query_vectors.return_value = {"vectors":[],"nextToken":"another-page"}
        client.meta.service_model.operation_model.return_value.input_shape.members = {"nextToken":object()}
        vectors = VectorStore("index","region",client=client)
        with self.assertRaises(ValueError):
            vectors.query([1.0]+[0.0]*511,"a"*64,H,"menu",max_pages=1)
        client.query_vectors.assert_called_once()
        client.query_vectors.reset_mock()
        client.query_vectors.side_effect = [{"vectors":[],"nextToken":"another-page"},{"vectors":[]}]
        self.assertEqual(vectors.query([1.0]+[0.0]*511,"a"*64,H,"menu"),[])
        self.assertEqual(client.query_vectors.call_count,2)  # Existing default preserved.
        from src.infrastructure import model
        with patch.object(model,"ChatBedrockConverse",return_value=object()) as factory:
            model.get_model(client_config=execution.SELECTOR_CONFIG)
            self.assertIs(factory.call_args.kwargs["config"], execution.SELECTOR_CONFIG)
            factory.reset_mock()
            model.get_model()
            self.assertNotIn("config",factory.call_args.kwargs)
        config = execution.SELECTOR_CONFIG
        self.assertEqual((config.connect_timeout,config.read_timeout,config.retries["total_max_attempts"]),(3,20,1))
        with patch.object(workflow,"structured_chain",return_value=object()) as factory:
            execution.make_selector(H)
        self.assertEqual(factory.call_args.args[2],1600)
        self.assertIs(factory.call_args.kwargs["client_config"],execution.SELECTOR_CONFIG)

    def test_factories_create_owned_sessions_in_their_worker_threads(self):
        from concurrent.futures import ThreadPoolExecutor
        sessions, barrier = [], threading.Barrier(2)
        def session():
            value = SimpleNamespace(owner=threading.get_ident())
            sessions.append(value)
            barrier.wait(timeout=2)
            return value
        with patch("boto3.session.Session",side_effect=session),ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(execution.make_scoped_retriever,rid) for rid in (H,S)]
            values = [future.result(timeout=3) for future in futures]
        self.assertEqual(len(sessions),2)
        self.assertNotEqual(sessions[0].owner,sessions[1].owner)
        for value in values:
            self.assertIs(value.store._session,value.vectors._session)
            self.assertIs(value.store._session,value.embeddings._session)
            self.assertEqual(value.embeddings.max_attempts,1)
            self.assertLessEqual(value.top_k,5)
        self.assertIsNot(values[0].store._session,values[1].store._session)

    def test_cancelling_pin_stops_subsequent_reads_after_inflight_call(self):
        reached, release, finished = threading.Event(),threading.Event(),threading.Event()
        retriever = self.harness.dependencies.pin_factory()
        original_active, original_pin = retriever.store.active,retriever.pin
        def active(key):
            reached.set()
            if not release.wait(timeout=2):
                raise TimeoutError("Fixture release missing")
            return original_active(key)
        def pin(**kwargs):
            try:
                return original_pin(**kwargs)
            finally:
                finished.set()
        retriever.store.active = active
        retriever.store.read_json = Mock(side_effect=AssertionError("No read after cancellation"))
        retriever.pin = pin
        deps = execution.ComparisonDependencies(pin_factory=lambda:retriever)
        async def run():
            task = asyncio.create_task(execution.answer_comparison(self.case.question,{},dependencies=deps))
            self.assertTrue(await asyncio.to_thread(reached.wait,2))
            task.cancel()
            try:
                with self.assertRaises(asyncio.CancelledError):
                    await task
            finally:
                release.set()
            self.assertTrue(await asyncio.to_thread(finished.wait,2))
        with self.offline():
            asyncio.run(run())
        retriever.store.read_json.assert_not_called()

    def test_outer_node_timeout_releases_no_unfinished_citations(self):
        from src.config import settings
        async def pending(*args,**kwargs):
            await asyncio.Event().wait()
        with patch.object(settings,"RAG_REQUEST_TIMEOUT_SECONDS",.01),\
             patch.object(workflow,"answer_document_question",side_effect=pending):
            result = asyncio.run(workflow.document_qa_node({"messages":[HumanMessage(content=self.case.question)]},{}))
        self.assertEqual(result["rag_status"],"unavailable")
        self.assertEqual(result["rag_mode"],"comparison")
        self.assertEqual(result["rag_pending_citations"],[])

    def test_both_provider_failures_are_unavailable_and_malformed_selector_is_invalid(self):
        simulation = self.case.simulation.model_copy(deep=True)
        for worker in simulation.workers:
            worker.fault = "provider_error"
        harness = evaluation.ComparisonHarness(self.manifest,simulation)
        with self.offline():
            outcome = asyncio.run(harness.run(self.case.question))
        self.assertEqual(outcome.status,"unavailable")
        self.assertEqual(outcome.citations,[])
        bad = execution.ComparisonDependencies(self.harness.dependencies.pin_factory,
            self.harness.dependencies.retriever_factory,lambda rid:SimpleNamespace(ainvoke=AsyncMock(return_value={"unknown":"PRIVATE"})))
        with self.offline():
            result = asyncio.run(execution.answer_comparison(self.case.question,{},dependencies=bad))
        self.assertEqual(result.status,"invalid_answer")
        self.assertNotIn("PRIVATE",result.text)

    def test_safe_spans_preserve_integrity_class_without_payload(self):
        observed = []
        class Obs:
            @contextmanager
            def create_span(self,name,attributes=None):
                observed.append((name,attributes))
                yield SimpleNamespace(set_attribute=lambda k,v:observed.append((k,v)))
        with cloud_clients_forbidden(), patch("src.infrastructure.rag_observability.get_observability_manager",return_value=Obs()):
            outcome = asyncio.run(self.harness.run(self.case.question))
        captured = json.dumps(observed)
        for text in [self.case.question,"RM32","RM36","Available at dinner", "SIMULATED_PRIVATE"]:
            self.assertNotIn(text,captured)
        self.assertIn("rag.comparison.aggregate",captured)
        from src.infrastructure.rag_observability import rag_span
        with self.assertRaises(EvidenceIntegrityError) as caught:
            with rag_span("fixture"):
                raise EvidenceIntegrityError("PRIVATE_PAYLOAD")
        self.assertNotIn("PRIVATE",str(caught.exception))

    def test_parent_graph_approval_scope_memory_and_private_checkpoint(self):
        from src.config import settings
        memory = SimpleNamespace(process_turn=Mock(return_value={"success":True}))
        saver = InMemorySaver()
        def single_retriever():
            value = self.harness.dependencies.pin_factory()
            value.vectors = SimulatedVectors(self.manifest)
            return value
        async def run():
            compiled = graph.create_orchestrator_graph(force_recreate=True)
            config = {"configurable":{"thread_id":"comparison-offline","actor_id":"comparison-demo"}}
            result = await compiled.ainvoke({"messages":[HumanMessage(content=self.case.question)],"rag_approved_scope":H},config)
            self.assertIsNone(result["rag_approved_scope"])
            self.assertEqual(len(result["rag_approved_citations"]),2)
            self.assertEqual(len(result["messages"]),2)
            self.assertTrue(result["messages"][-1].additional_kwargs["document_rag_response"])
            self.assertTrue({"manifest","rows","plan","result"}.isdisjoint(compiled.get_state(config).values))
            memory.process_turn.assert_called_once()
            self.assertEqual(memory.process_turn.call_args.kwargs["agent_response"],result["messages"][-1].content)
            followup = await compiled.ainvoke({"messages":[HumanMessage(content="What about its cancellation policy?")],
                "rag_pending_citations":[],"rag_approved_citations":[],"rag_mode":None},config)
            self.assertEqual(followup["rag_status"],"clarify")
            self.assertEqual(followup["rag_approved_citations"],[])
            self.assertIsNone(followup["rag_approved_scope"])
            explicit = await compiled.ainvoke({"messages":[HumanMessage(content="Harbor mushroom pasta price?")]},config)
            self.assertEqual(explicit["rag_approved_scope"],H)
            self.assertEqual(memory.process_turn.call_count,3)
        with self.offline(), patch.object(settings,"DOCUMENT_RAG_ENABLED",True), patch.object(graph,"_graph_instance",None),\
             patch.object(graph,"get_orchestrator_tools",return_value=[]),\
             patch.object(graph,"ShortTermMemory",return_value=SimpleNamespace(get_memory=lambda:saver)),\
             patch.object(nodes,"classify_with_jev",return_value=JevClassification("document_qa",.9)),\
             patch.object(nodes,"apply_output_guardrail",side_effect=lambda text:GuardrailResult(True,text,"NONE")),\
             patch.object(nodes,"get_memory_instance",return_value=memory),\
             patch.object(execution,"ComparisonDependencies",return_value=self.harness.dependencies),\
             patch.object(workflow,"make_retriever",side_effect=single_retriever),\
             patch.object(workflow,"structured_chain",return_value=self.harness.dependencies.selector_factory(H)):
            asyncio.run(run())

    def test_partial_guardrail_block_mask_scope_and_mode_reset(self):
        case = next(c for c in self.dataset.cases if c.id == "missing_right")
        outcome, _ = self.run_case(case)
        state = {"messages":[HumanMessage(content=case.question),AIMessage(content=outcome.text)],"intent":"document_qa",
                 "rag_mode":"comparison","rag_status":"partial","rag_pending_scope":None,
                 "rag_approved_scope":H,"rag_pending_citations":[c.model_dump() for c in outcome.citations]}
        for allowed, text in [(True,outcome.text),(True,"masked"),(False,"")]:
            with patch.object(nodes,"apply_output_guardrail",return_value=GuardrailResult(allowed,text,"NONE")):
                result = asyncio.run(nodes.output_guardrail_node(state,{}))
            self.assertEqual(bool(result["rag_approved_citations"]),allowed and text==outcome.text)
            if allowed:
                self.assertIsNone(result["rag_approved_scope"])
            else:
                self.assertNotIn("rag_approved_scope",result)
        fake = SimpleNamespace(ainvoke=AsyncMock(return_value={"messages":[AIMessage(content="safe")],"response_status":"approved"}))
        with patch.object(streaming,"create_orchestrator_graph",return_value=fake):
            asyncio.run(streaming.run_orchestrator_turn("hello",conversation_id="comparison-test"))
        self.assertIsNone(fake.ainvoke.await_args.kwargs["input"]["rag_mode"])


class ComparisonEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = evaluation.load_dataset()
        cls.grounded = evaluation.compile_dataset(cls.dataset)
        cls.observations = evaluation.run_offline(cls.dataset,cls.grounded)

    def test_full_independent_evaluation_and_omissions(self):
        report = evaluation.evaluate(self.dataset,self.observations,self.grounded)
        self.assertTrue(report["passed"])
        self.assertEqual(report["observed_cases"],20)
        self.assertFalse(evaluation.evaluate(self.dataset,self.observations[:-1],self.grounded)["passed"])
        for values in [self.observations+[self.observations[0]],
                       [self.observations[0].model_copy(update={"case_id":"unknown"})]]:
            with self.assertRaises(ValueError):
                evaluation.evaluate(self.dataset,values,self.grounded)

    def test_scorer_rejects_forged_coverage_math_and_citations(self):
        for changes in [{"text":"SECRET_ANSWER"},{"difference":"99"},{"cheaper_id":S},{"citations":[]},{"evidence":[]},
                        {"rows":list(reversed(self.observations[0].rows))},{"generation_id":"f"*64},
                        {"calls":self.observations[0].calls.model_copy(update={"selector":0})}]:
            values = copy.deepcopy(self.observations)
            values[0] = values[0].model_copy(update=changes)
            report = evaluation.evaluate(self.dataset,values,self.grounded)
            self.assertFalse(report["passed"],changes)
            self.assertNotIn("SECRET",json.dumps(report))

    def test_dataset_bounds_duplicate_unknown_and_nonfinite_inputs(self):
        original = self.dataset.model_dump()
        for data in [{**original,"extra":True},{**original,"cases":original["cases"][:-1]},
                     {**original,"cases":original["cases"]+[original["cases"][0]]},
                     {**original,"cases":original["cases"]*3}]:
            with self.assertRaises(ValueError):
                evaluation.Dataset.model_validate(data)
        with TemporaryDirectory() as directory:
            path = Path(directory)/"bad.json"
            path.write_text('{"n":NaN}')
            with self.assertRaises(ValueError):
                evaluation.read_json(path)
            path.write_bytes(b" "*(2*1024*1024+1))
            with self.assertRaises(ValueError):
                evaluation.read_json(path)

    def test_cli_exit_codes_and_report_hygiene(self):
        with TemporaryDirectory() as directory:
            output = Path(directory)/"report.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(evaluation.main(["--offline","--output",str(output)]),0)
            serialized = output.read_text()+output.with_suffix(".md").read_text()
            for raw in ["RM32","RM36",self.dataset.cases[0].question,"SIMULATED_PRIVATE","source_hash","session"]:
                self.assertNotIn(raw,serialized)
            with patch.object(evaluation,"run_offline",return_value=self.observations[:-1]),redirect_stdout(io.StringIO()):
                self.assertEqual(evaluation.main(["--offline","--output",str(output)]),1)
            bad = Path(directory)/"bad.json"
            bad.write_text('{"private":true}')
            with redirect_stdout(io.StringIO()) as captured:
                self.assertEqual(evaluation.main(["--offline","--dataset",str(bad),"--output",str(output)]),2)
            self.assertNotIn("private",captured.getvalue())


if __name__ == "__main__":
    unittest.main()
