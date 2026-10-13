"""One pin and one checked plan, followed by bounded isolated document workers."""
from __future__ import annotations

import asyncio
import json
import operator
import threading
import time
from dataclasses import dataclass
from typing import Annotated, Callable, TypedDict

from botocore.config import Config
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from src.application.document_rag.comparison_workflow import close_retriever, make_scoped_retriever
from src.application.document_rag.multipart import (
    CLARIFICATION, DISABLED, INVALID, UNAVAILABLE, PolicyConflict, aggregate_multipart, compile_multipart_request,
    policy_record, result_coverage, validate_multipart_plan, validate_passages, validate_task_selection,
)
from src.application.document_rag.retrieval import DocumentRetriever, router_catalog
from src.config import settings
from src.domain.document_multipart import MultipartPlan, MultipartPlanDraft, MultipartResult, MultipartTaskResult
from src.domain.document_rag import DocumentQuery, EvidenceIntegrityError, GenerationManifest, RagAnswerDraft, RagOutcome
from src.infrastructure.rag_observability import rag_span

PLANNER_CONFIG = Config(connect_timeout=3, read_timeout=5, retries={"total_max_attempts": 1})
SELECTOR_CONFIG = Config(connect_timeout=3, read_timeout=20, retries={"total_max_attempts": 1})


class OwnedStructuredCall:
    """Construct, invoke and close a fresh model in its owning synchronous thread."""

    def __init__(self, prompt, schema, tokens, client_config):
        self.prompt, self.schema, self.tokens, self.client_config = prompt, schema, tokens, client_config
        self.stopped = threading.Event()
        self.guard = lambda: None

    def bind_guard(self, guard):
        self.guard = guard

    def check(self):
        if self.stopped.is_set():
            raise TimeoutError("Model operation stopped")
        self.guard()

    def invoke(self, data, config):
        from langchain_core.messages import SystemMessage
        from langchain_core.prompts import ChatPromptTemplate
        from src.infrastructure.model import ModelType, get_model
        self.check()
        model = get_model(temperature=0, model_type=ModelType.EXTRACTION, client_config=self.client_config)
        try:
            self.check()
            model = model.model_copy(update={"max_tokens": self.tokens})
            chain = ChatPromptTemplate.from_messages([SystemMessage(content=self.prompt.prompt), ("human", "{payload}")]) | model.with_structured_output(self.schema)
            self.check()
            # invoke (not stream) ensures workers cannot publish provider tokens.
            return chain.invoke(data, config)
        finally:
            clients = {id(c): c for c in (getattr(model, "client", None), getattr(model, "bedrock_client", None)) if c is not None}
            for client in clients.values():
                try:
                    client.close()
                except Exception:
                    pass

    async def ainvoke(self, data, config):
        try:
            return await asyncio.to_thread(self.invoke, data, config)
        finally:
            self.stopped.set()


def make_planner():
    from src.domain.prompts import RAG_MULTIPART_PLAN_PROMPT
    return OwnedStructuredCall(RAG_MULTIPART_PLAN_PROMPT, MultipartPlanDraft, 1000, PLANNER_CONFIG)


def make_selector(_task):
    from src.domain.prompts import RAG_ANSWER_PROMPT
    return OwnedStructuredCall(RAG_ANSWER_PROMPT, RagAnswerDraft, 1600, SELECTOR_CONFIG)


@dataclass(frozen=True)
class MultipartDependencies:
    pin_factory: Callable = make_scoped_retriever
    retriever_factory: Callable = make_scoped_retriever
    planner_factory: Callable = make_planner
    selector_factory: Callable = make_selector
    result_observer: Callable | None = None
    task_observer: Callable | None = None  # Test-only completed-task observation.


class MultipartState(TypedDict):
    plan: MultipartPlan
    manifest: GenerationManifest
    rows: Annotated[list[MultipartTaskResult], operator.add]
    result: MultipartResult


def build_multipart_graph(dependencies, deadline, ledger, clock=time.monotonic, progress=None):
    semaphore = asyncio.Semaphore(2)
    progress = progress if progress is not None else {}

    async def worker(state, config):
        task, manifest = state["task"], state["manifest"]
        stopped, started = threading.Event(), [False]
        selected = [False]
        progress[task.task_id] = started

        def worker_clock():
            if stopped.is_set():
                raise TimeoutError("Worker stopped")
            return clock()

        def check():
            DocumentRetriever.check_deadline(deadline, worker_clock)

        def retrieve():
            check()
            retriever = dependencies.retriever_factory(task.restaurant_id)
            try:
                if not 1 <= retriever.top_k <= 5 or not 0 < retriever.max_characters <= 9000:
                    raise EvidenceIntegrityError("Task retrieval exceeds bounds")
                check()
                started[0] = True
                query = (f"{task.item} listed price at {task.restaurant_name}" if task.item else
                         f"reservation cancellation timing and fee policy at {task.restaurant_name}")
                return retriever.retrieve(DocumentQuery(query=query, restaurant_id=task.restaurant_id, document_type=task.document_type),
                                          manifest, deadline=deadline, clock=worker_clock, max_pages=1)
            finally:
                close_retriever(retriever)

        def row(status, reason):
            return MultipartTaskResult(task=task, status=status, reason=reason, retrieval_started=started[0])

        async def run():
            check()
            evidence = await asyncio.to_thread(retrieve)
            validate_passages(task, evidence, manifest)
            if not evidence:
                return row("missing", "missing_evidence")
            record = None
            if task.criterion == "cancellation_policy":
                record, reason = policy_record(task, evidence, manifest)
                if record is None:
                    return row("missing", reason)
            check()
            selector = dependencies.selector_factory(task)
            if hasattr(selector, "bind_guard"):
                selector.bind_guard(check)
            question = (f"Select exactly one complete {task.item} menu record with its price at {task.restaurant_name}. "
                        "Keep all adjacent dietary, timing and other qualifiers." if task.item else
                        f"Select exactly one complete Reservations and cancellation section body at {task.restaurant_name}. "
                        "Keep all timing conditions and fees, including sentences needed to explain 'Later'. Omit only the section heading.")
            check()
            try:
                selected[0] = True
                draft = await selector.ainvoke({"payload": json.dumps({"question": question,
                    "evidence": [{"chunk_id": e.chunk_id, "text": e.text} for e in evidence]}, ensure_ascii=False)}, config)
                check()
                return validate_task_selection(task, draft, evidence, manifest, record)
            except ValueError:
                return row("invalid", "invalid_selection")

        try:
            remaining = deadline-clock()
            if remaining <= 0:
                result = row("unavailable", "deadline_exhausted")
            else:
                async with asyncio.timeout(remaining):
                    async with semaphore:
                        try:
                            with rag_span("rag.multipart.worker", {"rag.task_id": task.task_id, "rag.criterion": task.criterion,
                                "rag.restaurant": task.restaurant_id, "rag.generation": manifest.generation_id}) as span:
                                result = await run()
                                if span:
                                    span.set_attribute("rag.status", result.status)
                                    span.set_attribute("rag.reason", result.reason)
                        finally:
                            stopped.set()
        except asyncio.CancelledError:
            stopped.set()
            raise
        except PolicyConflict:
            result = row("invalid", "conflicting_evidence")
        except EvidenceIntegrityError:
            result = row("invalid", "invalid_evidence")
        except TimeoutError:
            result = row("unavailable", "deadline_exhausted")
        except Exception:
            result = row("unavailable", "provider_error")
        finally:
            stopped.set()
        if task.task_id in ledger:
            raise EvidenceIntegrityError("Duplicate completed task")
        ledger[task.task_id] = result
        with rag_span("rag.multipart.worker.complete", {"rag.task_id": task.task_id, "rag.criterion": task.criterion,
            "rag.restaurant": task.restaurant_id, "rag.generation": manifest.generation_id,
            "rag.status": result.status, "rag.reason": result.reason,
            "rag.retrieval_attempts": int(started[0]), "rag.selector_attempts": int(selected[0])}):
            pass
        if dependencies.task_observer:
            dependencies.task_observer(result)
        return {"rows": [result]}

    def dispatch(state):
        return [Send("document_worker", {"task": task, "manifest": state["manifest"]}) for task in state["plan"].tasks]

    def aggregate(state):
        with rag_span("rag.multipart.aggregate", {"rag.required": len(state["plan"].tasks)}) as span:
            try:
                result = aggregate_multipart(state["plan"], state["rows"], state["manifest"])
            except ValueError:
                raise EvidenceIntegrityError("Invalid aggregated task results") from None
            if span:
                span.set_attribute("rag.supported", result.supported)
                span.set_attribute("rag.status", result.status)
                span.set_attribute("rag.citation_count", len(result.citations))
        return {"result": result}

    graph = StateGraph(MultipartState)
    graph.add_node("dispatch", lambda _: {})
    graph.add_node("document_worker", worker)
    graph.add_node("aggregate", aggregate)
    graph.add_edge(START, "dispatch")
    graph.add_conditional_edges("dispatch", dispatch, ["document_worker"])
    graph.add_edge("document_worker", "aggregate")
    graph.add_edge("aggregate", END)
    return graph.compile(checkpointer=False, name="document_multipart")


async def answer_multipart(question, config, *, dependencies=None, deadline=None, clock=time.monotonic):
    if not settings.DOCUMENT_RAG_ENABLED or not settings.DOCUMENT_MULTIPART_ENABLED:
        return RagOutcome(mode="multipart", status="disabled", text=DISABLED)
    request = compile_multipart_request(question, router_catalog())
    if request is None:
        return RagOutcome(mode="multipart", status="clarify", text=CLARIFICATION)
    dependencies = dependencies or MultipartDependencies()
    deadline = deadline if deadline is not None else clock()+settings.RAG_REQUEST_TIMEOUT_SECONDS
    pin_stopped = threading.Event()

    def pin_clock():
        if pin_stopped.is_set():
            raise TimeoutError("Pin stopped")
        return clock()

    def pin():
        DocumentRetriever.check_deadline(deadline-2, pin_clock)
        retriever = dependencies.pin_factory()
        try:
            return retriever.pin(deadline=deadline-2, clock=pin_clock)
        finally:
            close_retriever(retriever)

    try:
        remaining = deadline-2-clock()
        if remaining <= 0:
            raise TimeoutError("Pin budget exhausted")
        async with asyncio.timeout(remaining):
            manifest = await asyncio.to_thread(pin)
        # Check pinned catalog before spending the planner call.
        pinned = compile_multipart_request(question, manifest)
        if pinned is None or pinned.tasks != request.tasks:
            raise EvidenceIntegrityError("Pinned catalog differs from admitted scope")
        planner_deadline = min(clock()+5, deadline-2)
        DocumentRetriever.check_deadline(planner_deadline, clock)
        with rag_span("rag.multipart.plan", {"rag.required": len(request.tasks), "rag.generation": manifest.generation_id,
                                             "rag.planner_attempts": 1}):
            planner = dependencies.planner_factory()
            if hasattr(planner, "bind_guard"):
                planner.bind_guard(lambda: DocumentRetriever.check_deadline(planner_deadline, clock))
            try:
                async with asyncio.timeout(planner_deadline-clock()):
                    draft = await planner.ainvoke({"payload": json.dumps({"question": request.question,
                        "restaurants": [{"restaurant_id": r.restaurant_id, "name": r.name} for r in manifest.restaurants],
                        "allowed_criteria": ["menu_item_price", "cancellation_policy"]}, ensure_ascii=False)}, config)
                DocumentRetriever.check_deadline(planner_deadline, clock)
                plan = validate_multipart_plan(request, draft, manifest)
            except ValueError:
                return RagOutcome(mode="multipart", status="invalid_answer", text=INVALID, generation_id=manifest.generation_id)
        worker_deadline = min(clock()+45, deadline-2)
        ledger, progress = {}, {}
        graph = build_multipart_graph(dependencies, worker_deadline, ledger, clock, progress)
        try:
            DocumentRetriever.check_deadline(worker_deadline, clock)
            # Workers stop provider operations at the shared deadline. Give the
            # graph a bounded part of the assembly reserve to account for queued
            # rows instead of cancelling the executor at that same instant.
            graph_deadline = min(worker_deadline+.25, deadline-.25)
            async with asyncio.timeout(graph_deadline-clock()):
                result = (await graph.ainvoke({"plan": plan, "manifest": manifest, "rows": []},
                                             {**config, "max_concurrency": 2}))["result"]
        except TimeoutError:
            rows = [ledger.get(t.task_id) or MultipartTaskResult(task=t, status="unavailable", reason="deadline_exhausted",
                    retrieval_started=progress.get(t.task_id, [False])[0]) for t in plan.tasks]
            try:
                result = aggregate_multipart(plan, rows, manifest)
            except ValueError:
                raise EvidenceIntegrityError("Invalid deadline task results") from None
        if dependencies.result_observer:
            dependencies.result_observer(result)
        return RagOutcome(mode="multipart", status=result.status, text=result.text, generation_id=manifest.generation_id,
                          retrieval_count=sum(r.retrieval_started for r in result.rows), citations=list(result.citations),
                          coverage=result_coverage(result) if result.status in {"answered", "partial", "unavailable", "insufficient_evidence"} else None)
    except asyncio.CancelledError:
        raise
    except EvidenceIntegrityError:
        return RagOutcome(mode="multipart", status="invalid_answer", text=INVALID)
    except Exception:
        return RagOutcome(mode="multipart", status="unavailable", text=UNAVAILABLE)
    finally:
        pin_stopped.set()
