"""Stateless LangGraph comparison: one pin, two scoped workers, one final result."""
from __future__ import annotations

import asyncio
import json
import operator
import time
import threading
from dataclasses import dataclass
from typing import Annotated, Callable, TypedDict

from botocore.config import Config
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from src.config import settings
from src.application.document_rag.comparison import (
    CLARIFICATION, INVALID, UNAVAILABLE, aggregate_comparison, plan_comparison, validate_selection,
)
from src.application.document_rag.retrieval import DocumentRetriever
from src.domain.document_comparison import ComparisonPlan, ComparisonResult, ComparisonRow
from src.domain.document_rag import DocumentQuery, EvidenceIntegrityError, GenerationManifest, RagOutcome
from src.infrastructure.rag_observability import rag_span

SELECTOR_CONFIG = Config(connect_timeout=3, read_timeout=20, retries={"total_max_attempts": 1})


def make_scoped_retriever(_restaurant_id=None):
    """Called inside the owning synchronous task; the session never crosses threads."""
    import boto3
    from src.infrastructure.document_store import DocumentStore
    from src.infrastructure.embeddings import TitanEmbeddings
    from src.infrastructure.vector_store import VectorStore
    if settings.RAG_EMBEDDING_MODEL_ID != "amazon.titan-embed-text-v2:0" or settings.RAG_EMBEDDING_DIMENSIONS != 512:
        raise ValueError("Incompatible comparison embeddings")
    session = boto3.session.Session()
    return DocumentRetriever(
        DocumentStore(settings.RAG_DOCUMENT_BUCKET, settings.AWS_REGION, session=session),
        VectorStore(settings.RAG_VECTOR_INDEX_ARN, settings.AWS_REGION, session=session),
        TitanEmbeddings(settings.AWS_REGION, session=session, max_attempts=1),
        active_key=settings.RAG_ACTIVE_MANIFEST_KEY, top_k=min(settings.RAG_TOP_K, 5),
        max_characters=settings.RAG_MAX_CONTEXT_CHARACTERS,
    )


def make_selector(_restaurant_id):
    from src.application.document_rag.workflow import structured_chain
    from src.domain.document_rag import RagAnswerDraft
    from src.domain.prompts import RAG_ANSWER_PROMPT
    return structured_chain(RAG_ANSWER_PROMPT, RagAnswerDraft, 1600, client_config=SELECTOR_CONFIG)


def close_retriever(retriever):
    # Only close initialized, operation-owned clients. Never trigger lazy construction.
    for adapter in (retriever.store, retriever.vectors, retriever.embeddings):
        client = getattr(adapter, "_client", None)
        if client is not None:
            try:
                client.close()
            except Exception:
                pass  # Cleanup cannot replace a validated outcome or leak provider text.


@dataclass(frozen=True)
class ComparisonDependencies:
    pin_factory: Callable = make_scoped_retriever
    retriever_factory: Callable = make_scoped_retriever
    selector_factory: Callable = make_selector
    result_observer: Callable | None = None  # Optional offline observation; absent in production.


class ComparisonState(TypedDict):
    plan: ComparisonPlan
    manifest: GenerationManifest
    rows: Annotated[list[ComparisonRow], operator.add]
    result: ComparisonResult


def build_comparison_graph(dependencies, deadline, clock=time.monotonic):
    async def worker(state, config):
        rid, plan, manifest = state["restaurant_id"], state["plan"], state["manifest"]
        started = [False]
        stopped = threading.Event()

        def worker_clock():
            if stopped.is_set():
                raise TimeoutError("Comparison worker stopped")
            return clock()

        def retrieve():
            DocumentRetriever.check_deadline(deadline, worker_clock)
            retriever = dependencies.retriever_factory(rid)
            try:
                if not 1 <= retriever.top_k <= 5 or not 0 < retriever.max_characters <= 9000:
                    raise ValueError("Comparison retrieval configuration exceeds limits")
                DocumentRetriever.check_deadline(deadline, worker_clock)
                started[0] = True
                name = next(r.name for r in manifest.restaurants if r.restaurant_id == rid)
                query = DocumentQuery(query=f"{plan.item} listed price at {name}", restaurant_id=rid, document_type="menu")
                return retriever.retrieve(query, manifest, deadline=deadline, clock=worker_clock, max_pages=1)
            finally:
                close_retriever(retriever)

        def row(status, reason):
            return {"rows": [ComparisonRow(restaurant_id=rid, status=status, reason=reason, retrieval_started=started[0])]}

        try:
            remaining = deadline - clock()
            if remaining <= 0:
                return row("unavailable", "deadline_exhausted")
            async with asyncio.timeout(remaining):
                with rag_span("rag.comparison.worker", {"rag.restaurant": rid, "rag.generation": plan.generation_id}):
                    evidence = await asyncio.to_thread(retrieve)
                    if not evidence:
                        return row("missing", "missing_evidence")
                    DocumentRetriever.check_deadline(deadline, clock)
                    selector = dependencies.selector_factory(rid)
                    name = next(r.name for r in manifest.restaurants if r.restaurant_id == rid)
                    payload = {"question": f"Select exactly one complete {plan.item} menu record with its listed price at {name}. "
                                           "Include all adjacent dietary, timing and other qualifiers; no other item.",
                               "evidence": [{"chunk_id": item.chunk_id, "text": item.text} for item in evidence]}
                    try:
                        with rag_span("rag.comparison.select", {"rag.restaurant": rid}):
                            # Catch schema/parser failures before the span sanitizes their type.
                            try:
                                draft = await selector.ainvoke({"payload": json.dumps(payload, ensure_ascii=False)}, config)
                            except ValueError:
                                return row("invalid", "invalid_selection")
                        DocumentRetriever.check_deadline(deadline, clock)
                        with rag_span("rag.comparison.validate", {"rag.restaurant": rid}):
                            try:
                                validated = validate_selection(plan, rid, draft, evidence, manifest)
                            except ValueError:
                                return row("invalid", "invalid_selection")
                        return {"rows": [validated]}
                    except asyncio.CancelledError:
                        raise
        except asyncio.CancelledError:
            stopped.set()
            raise
        except EvidenceIntegrityError:
            return row("invalid", "invalid_evidence")
        except TimeoutError:
            stopped.set()
            return row("unavailable", "deadline_exhausted")
        except Exception:
            return row("unavailable", "provider_error")

    def dispatch(state):
        return [Send("comparison_worker", {"restaurant_id": rid, "plan": state["plan"],
                                           "manifest": state["manifest"].model_copy(deep=True)})
                for rid in state["plan"].restaurant_ids]

    def aggregate(state):
        with rag_span("rag.comparison.aggregate", {"rag.branch_count": len(state["rows"])}) as span:
            try:
                result = aggregate_comparison(state["plan"], state["rows"], state["manifest"])
            except ValueError:
                raise EvidenceIntegrityError("Invalid aggregated comparison") from None
            if span:
                for key, value in {"rag.coverage": result.coverage, "rag.status": result.status,
                                   "rag.citation_count": len(result.citations)}.items():
                    span.set_attribute(key, value)
            return {"result": result}

    graph = StateGraph(ComparisonState)
    graph.add_node("dispatch", lambda _state: {})
    graph.add_node("comparison_worker", worker)
    graph.add_node("aggregate", aggregate)
    graph.add_edge(START, "dispatch")
    graph.add_conditional_edges("dispatch", dispatch, ["comparison_worker"])
    graph.add_edge("comparison_worker", "aggregate")
    graph.add_edge("aggregate", END)
    return graph.compile(checkpointer=False, name="document_comparison")


async def answer_comparison(question, config, *, dependencies=None, deadline=None, clock=time.monotonic):
    dependencies = dependencies or ComparisonDependencies()
    deadline = deadline if deadline is not None else clock() + settings.RAG_REQUEST_TIMEOUT_SECONDS
    pin_stopped = threading.Event()

    def pin_clock():
        if pin_stopped.is_set():
            raise TimeoutError("Comparison pin stopped")
        return clock()

    def pin():
        DocumentRetriever.check_deadline(deadline, pin_clock)
        retriever = dependencies.pin_factory()
        try:
            return retriever.pin(deadline=deadline, clock=pin_clock)
        finally:
            close_retriever(retriever)

    try:
        with rag_span("rag.comparison.plan", {"rag.criterion": "menu_item_price"}):
            manifest = await asyncio.to_thread(pin)
            plan = plan_comparison(question, manifest)
        if plan is None:
            return RagOutcome(status="clarify", text=CLARIFICATION, generation_id=manifest.generation_id)
        worker_deadline = min(clock() + 45, deadline - 2)
        if worker_deadline <= clock():
            return RagOutcome(status="unavailable", text=UNAVAILABLE, generation_id=manifest.generation_id)
        graph = build_comparison_graph(dependencies, worker_deadline, clock)
        result = (await graph.ainvoke({"plan": plan, "manifest": manifest, "rows": []},
                                     {**config, "max_concurrency": 2}))["result"]
        if dependencies.result_observer:
            dependencies.result_observer(result)
        candidate = None
        if settings.DOCUMENT_FOLLOWUPS_ENABLED and result.status in {"answered", "partial"}:
            from src.application.document_rag.conversation import context_draft
            candidate = context_draft(plan.restaurant_ids, plan.item, "comparison", plan.generation_id)
        return RagOutcome(status=result.status, text=result.text, generation_id=plan.generation_id,
                          retrieval_count=sum(row.retrieval_started for row in result.rows), citations=result.citations,
                          mode="comparison" if candidate else None, context_candidate=candidate)
    except asyncio.CancelledError:
        pin_stopped.set()
        raise
    except EvidenceIntegrityError:
        return RagOutcome(status="invalid_answer", text=INVALID)
    except Exception:
        return RagOutcome(status="unavailable", text=UNAVAILABLE)
