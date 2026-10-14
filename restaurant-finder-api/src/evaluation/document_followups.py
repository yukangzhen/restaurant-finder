"""Offline parent-graph conversations with scripted providers and independent gold."""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from typing import Literal
from unittest.mock import AsyncMock, Mock, patch

from pydantic import Field, model_validator

from src.domain.document_rag import DocumentCitation, canonical_text
from src.evaluation.rag import API_ROOT, GoldQuote, Script, StrictModel, escaped, expected_citations, read_json
from src.evaluation.rag_offline import MemoryStore, NoTelemetry, ScriptedSelector, SimulatedEmbeddings, SimulatedVectors, cloud_clients_forbidden

DATASET_PATH = Path(__file__).parent / "datasets/document_followups.json"


class Counts(StrictModel):
    pin: int = Field(default=0, ge=0, le=1)
    planner: int = Field(default=0, ge=0, le=1)
    embedding: int = Field(default=0, ge=0, le=4)
    retrieval: int = Field(default=0, ge=0, le=4)
    selector: int = Field(default=0, ge=0, le=4)
    rewrite: int = Field(default=0, ge=0, le=1)
    chunk_reads: int = Field(default=0, ge=0, le=20)
    jev: int = Field(default=0, ge=0, le=1)
    fallback: int = Field(default=0, ge=0, le=1)
    moderation: int = Field(default=1, ge=0, le=1)
    memory: int = Field(default=1, ge=0, le=1)


class Scope(StrictModel):
    restaurant_id: str = Field(pattern=r"^demo-[a-z0-9-]+$")
    document_type: Literal["menu", "policy"] | None = None
    max_pages: int | None = Field(default=None, ge=1, le=10)


class Expected(StrictModel):
    status: Literal["answered", "partial", "clarify", "disabled", "unavailable", "invalid_answer", "insufficient_evidence"] | None
    mode: Literal["single", "comparison", "multipart"] | None
    response_status: Literal["approved", "blocked"] = "approved"
    render_kind: Literal["single", "comparison", "multipart", "literal"]
    render_data: dict = Field(default_factory=dict)
    quotes: list[GoldQuote] = Field(default_factory=list, max_length=4)
    text: str | None = Field(default=None, max_length=15000)
    generation_present: bool = True
    context_targets: list[str] = Field(default_factory=list, max_length=2)
    context_item: str | None = None
    pending: bool = False
    decision: Literal["resolved", "clarify"] | None = None
    effective_targets: list[str] = Field(default_factory=list, max_length=2)
    effective_item: str | None = None
    calls: Counts
    scopes: list[Scope] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def coherent(self):
        if self.render_kind == "literal" and (not self.text or self.quotes):
            raise ValueError("Literal gold requires text and no sources")
        if self.render_kind == "single" and (not self.quotes or self.render_data or self.text):
            raise ValueError("Single gold requires explicit records")
        return self


class Worker(StrictModel):
    restaurant_id: str
    criterion: Literal["menu_item_price", "cancellation_policy"]
    selector: Script


class Simulation(StrictModel):
    router_intent: Literal["document_qa", "simple", "off_topic"] = "document_qa"
    jev_failure: bool = False
    single: Script | None = None
    workers: list[Worker] = Field(default_factory=list, max_length=4)
    planner: dict = Field(default_factory=dict)
    moderation: Literal["unchanged", "mask", "block"] = "unchanged"
    simple_text: str = "You're welcome."
    followups_enabled: bool = True
    multipart_enabled: bool = True
    pointer_changes: bool = False


class Turn(StrictModel):
    question: str = Field(min_length=1, max_length=1000)
    corpus: Literal["corpus.json", "corpus-v2.json"] = "corpus-v2.json"
    thread: str = Field(default="main", pattern=r"^[a-z0-9_-]{1,24}$")
    actor: str = Field(default="portfolio", pattern=r"^[a-z0-9_-]{1,24}$")
    expected: Expected
    simulation: Simulation


class Variant(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_-]{1,24}$")
    turns: list[Turn] = Field(min_length=1, max_length=6)


class Case(StrictModel):
    id: str = Field(pattern=r"^F(?:0[1-9]|1[0-9]|2[0-4])$")
    variants: list[Variant] = Field(min_length=1, max_length=4)


class Dataset(StrictModel):
    schema_version: Literal[1]
    name: Literal["fictional-document-followups"]
    cases: list[Case] = Field(min_length=24, max_length=24)

    @model_validator(mode="after")
    def complete(self):
        if [c.id for c in self.cases] != [f"F{i:02}" for i in range(1, 25)]:
            raise ValueError("Dataset must contain ordered F01-F24 exactly once")
        if any(len({v.id for v in c.variants}) != len(c.variants) for c in self.cases):
            raise ValueError("Duplicate variant")
        return self


def load_dataset(path=DATASET_PATH):
    return Dataset.model_validate(read_json(path))


def compile_dataset(dataset):
    from src.application.document_rag.ingestion import prepare_generation
    manifests = {name: prepare_generation(API_ROOT / "sample_documents" / name)[0]
                 for name in {t.corpus for c in dataset.cases for v in c.variants for t in v.turns}}
    gold = {}
    for case in dataset.cases:
        for variant in case.variants:
            for i, turn in enumerate(variant.turns):
                manifest = manifests[turn.corpus]
                records = list(turn.expected.quotes)
                if turn.expected.render_kind == "comparison":
                    from src.evaluation.document_comparison import Expectation
                    reference = Expectation.model_validate(turn.expected.render_data)
                    records = [r.quote for r in reference.rows if r.quote]
                elif turn.expected.render_kind == "multipart":
                    from src.evaluation.document_multipart import Expected as MultipartExpected
                    reference = MultipartExpected.model_validate(turn.expected.render_data)
                    records = [t.quote for t in reference.tasks if t.quote]
                quotes = []
                for record in records:
                    matches = [c for c in manifest.chunks if c.document_id == record.document_id
                        and c.version == record.version and canonical_text(record.quote) in c.text
                        and all(getattr(c, f) == getattr(record, f) for f in ("page", "section", "line_start", "line_end"))]
                    if len(matches) != 1:
                        raise ValueError("Conversation gold is not uniquely grounded")
                    quotes.append((record, matches[0]))
                gold[(case.id, variant.id, i)] = manifest, quotes
    return gold


class QuietTelemetry(NoTelemetry):
    def record_workflow_step(self, **_kwargs):
        pass

    def record_memory_operation(self, *_args, **_kwargs):
        pass


class TurnProviders:
    """Only simulation scripts and source fixtures enter provider implementations."""
    def __init__(self, manifest, simulation):
        from src.application.document_rag.retrieval import DocumentRetriever
        self.simulation, self.manifest = simulation, manifest
        self.pin = self.chunk_reads = self.planner = self.rewrite = self.jev = self.fallback = self.moderation = 0
        self.retrievers, self.selectors, self.scopes, self.saved = [], [], [], []
        outer = self

        class Store(MemoryStore):
            def active(self, key):
                outer.pin += 1
                pointer, etag = super().active(key)
                if simulation.pointer_changes:
                    self.pointer = self.pointer.model_copy(update={"generation_id": "f" * 64})
                return pointer, etag

            def read_json(self, key):
                if "/chunks/" in key:
                    outer.chunk_reads += 1
                return super().read_json(key)

        store = Store(manifest)

        class Vectors(SimulatedVectors):
            def query(self, vector, generation, rid, kind, top_k, *, max_pages=None):
                outer.scopes.append({"restaurant_id": rid, "document_type": kind, "max_pages": max_pages,
                                     "generation_id": generation})
                return super().query(vector, generation, rid, kind, top_k)

        class Retriever(DocumentRetriever):
            def __init__(self):
                super().__init__(store, Vectors(manifest), SimulatedEmbeddings(manifest.config))
                outer.retrievers.append(self)

        self.retriever = Retriever

    def selector(self, rid=None, criterion=None):
        script = self.simulation.single if rid is None else next(
            w.selector for w in self.simulation.workers if w.restaurant_id == rid and w.criterion == criterion)
        if script is None:
            raise AssertionError("Unexpected single selector")
        value = ScriptedSelector(script, self.manifest)
        self.selectors.append(value)
        return value

    async def classify(self, *_args, **_kwargs):
        from src.infrastructure.jev_router import JevClassification, JevRouterUnavailable
        self.jev += 1
        if self.simulation.jev_failure:
            raise JevRouterUnavailable("offline")
        return JevClassification(self.simulation.router_intent, .9)

    async def classify_fallback(self, *_args, **_kwargs):
        from langchain_core.messages import AIMessage
        self.fallback += 1
        return AIMessage(content=self.simulation.router_intent)

    def moderate(self, text):
        from src.infrastructure.guardrails import GuardrailResult
        self.moderation += 1
        return GuardrailResult(self.simulation.moderation != "block",
            "Masked response." if self.simulation.moderation == "mask" else text, "NONE")

    def save(self, **values):
        self.saved.append(values)
        return {"success": True}

    def factories(self):
        outer = self

        class Planner:
            async def ainvoke(self, *_args, **_kwargs):
                outer.planner += 1
                return copy.deepcopy(outer.simulation.planner)

        class Rewrite:
            async def ainvoke(self, *_args, **_kwargs):
                outer.rewrite += 1
                raise AssertionError("Unexpected query rewrite")

        def structured(prompt, *_args, **_kwargs):
            from src.domain.prompts import RAG_QUERY_PROMPT
            return Rewrite() if prompt is RAG_QUERY_PROMPT else outer.selector()

        return Planner, structured

    def counts(self):
        return Counts(pin=self.pin, planner=self.planner, chunk_reads=self.chunk_reads, jev=self.jev,
            fallback=self.fallback, moderation=self.moderation, memory=len(self.saved), rewrite=self.rewrite,
            embedding=sum(r.embeddings.attempts for r in self.retrievers),
            retrieval=sum(r.vectors.attempts for r in self.retrievers), selector=sum(s.attempts for s in self.selectors)).model_dump()


def run_offline(dataset, gold):
    """Execute real parent turns; never read Expected fields to prepare providers."""
    from langchain_core.messages import AIMessage
    from langgraph.checkpoint.memory import InMemorySaver
    from src.application.document_rag import workflow, comparison_workflow, multipart_workflow
    from src.application.orchestrator import streaming
    from src.application.orchestrator.workflow import graph, nodes
    from src.config import settings
    observations = []
    telemetry = QuietTelemetry()
    with cloud_clients_forbidden(), ExitStack() as common:
        common.enter_context(patch.object(graph, "get_orchestrator_tools", return_value=[]))
        common.enter_context(patch("src.infrastructure.rag_observability.get_observability_manager", return_value=telemetry))
        common.enter_context(patch.object(nodes, "get_observability_manager", return_value=telemetry))
        common.enter_context(patch.object(workflow, "get_observability_manager", return_value=telemetry))
        for case in dataset.cases:
            variants = []
            for variant in case.variants:
                saver = InMemorySaver()
                with patch.object(graph, "_graph_instance", None), patch.object(graph, "ShortTermMemory",
                        return_value=SimpleNamespace(get_memory=lambda: saver)):
                    compiled = graph.create_orchestrator_graph(force_recreate=True)
                turns = []
                for i, turn in enumerate(variant.turns):
                    manifest = gold[(case.id, variant.id, i)][0]
                    providers = TurnProviders(manifest, turn.simulation)
                    planner, structured = providers.factories()
                    cmp_deps = SimpleNamespace(pin_factory=providers.retriever,
                        retriever_factory=lambda _rid: providers.retriever(),
                        selector_factory=lambda rid: providers.selector(rid, "menu_item_price"), result_observer=None)
                    mp_deps = SimpleNamespace(pin_factory=providers.retriever,
                        retriever_factory=lambda _rid: providers.retriever(), planner_factory=planner,
                        selector_factory=lambda task: providers.selector(task.restaurant_id, task.criterion),
                        result_observer=None, task_observer=None)
                    thread = f"followup-{case.id}-{variant.id}-{turn.thread}"
                    config = {"configurable": {"thread_id": thread, "actor_id": turn.actor}}
                    with ExitStack() as step:
                        for name, value in {"DOCUMENT_RAG_ENABLED": True,
                                "DOCUMENT_FOLLOWUPS_ENABLED": turn.simulation.followups_enabled,
                                "DOCUMENT_MULTIPART_ENABLED": turn.simulation.multipart_enabled}.items():
                            step.enter_context(patch.object(settings, name, value))
                        step.enter_context(patch.object(streaming, "create_orchestrator_graph", return_value=compiled))
                        step.enter_context(patch.object(nodes, "classify_with_jev", side_effect=providers.classify))
                        step.enter_context(patch.object(nodes, "get_router_chain", return_value=SimpleNamespace(ainvoke=providers.classify_fallback)))
                        step.enter_context(patch.object(nodes, "get_simple_response_chain", return_value=SimpleNamespace(
                            ainvoke=AsyncMock(return_value=AIMessage(content=turn.simulation.simple_text)))))
                        step.enter_context(patch.object(nodes, "apply_output_guardrail", side_effect=providers.moderate))
                        step.enter_context(patch.object(nodes, "get_memory_instance", return_value=SimpleNamespace(process_turn=providers.save)))
                        step.enter_context(patch.object(workflow, "make_retriever", side_effect=providers.retriever))
                        step.enter_context(patch.object(workflow, "structured_chain", side_effect=structured))
                        step.enter_context(patch.object(comparison_workflow, "ComparisonDependencies", return_value=cmp_deps))
                        step.enter_context(patch.object(multipart_workflow, "MultipartDependencies", return_value=mp_deps))
                        result = asyncio.run(streaming.run_orchestrator_turn(turn.question, conversation_id=thread, actor_id=turn.actor))
                    state = compiled.get_state(config).values
                    resolution = state.get("rag_followup_resolution") or {}
                    context = state.get("rag_approved_context") or {}
                    turns.append({"status": state.get("rag_status"), "mode": state.get("rag_mode"),
                        "response_status": state.get("response_status"), "text": result.text,
                        "generation": state.get("rag_generation"), "citations": [c.model_dump() for c in result.citations],
                        "context_targets": context.get("restaurant_ids", []), "context_item": context.get("item"),
                        "pending": bool(state.get("rag_approved_followup")), "decision": resolution.get("decision"),
                        "effective_targets": resolution.get("restaurant_ids", []), "effective_item": resolution.get("item"),
                        "calls": providers.counts(), "scopes": providers.scopes,
                        "original_memory": all(s["user_input"] == turn.question and s["agent_response"] == result.text for s in providers.saved),
                        "private_state": {"manifest", "plan", "rows", "result", "evidence"}.isdisjoint(state),
                        "candidates_cleared": state.get("rag_pending_context") is None and state.get("rag_pending_followup") is None})
                variants.append({"variant_id": variant.id, "turns": turns})
            observations.append({"case_id": case.id, "variants": variants})
    return observations


def expected_text(expected, manifest, gold):
    if expected.render_kind == "literal":
        return expected.text
    if expected.render_kind == "comparison":
        from src.evaluation.document_comparison import Expectation, expected_text as render
        return render(SimpleNamespace(expected=Expectation.model_validate(expected.render_data)), manifest, gold)
    if expected.render_kind == "multipart":
        from src.evaluation.document_multipart import Expected as MultipartExpected, expected_text as render
        return render(SimpleNamespace(expected=MultipartExpected.model_validate(expected.render_data), legacy_comparison=False), manifest, gold)
    names = {r.restaurant_id: r.name for r in manifest.restaurants}
    lines = ["According to the fictional demo documents:"]
    for i, (record, chunk) in enumerate(gold, 1):
        location = f"page {chunk.page}" if chunk.page else f"section {chunk.section}, lines {chunk.line_start}-{chunk.line_end}"
        provenance = f"{names[chunk.restaurant_id]}; {record.document_id}; {location}; version {record.version}; generation {manifest.generation_id[:12]}"
        lines.extend(["", f'> "{escaped(record.quote)}"', "", f"Source: Source {i} — {escaped(provenance)}"])
    return "\n".join(lines)


def evaluate(dataset, observations, gold):
    ids = [o["case_id"] for o in observations]
    if len(set(ids)) != len(ids) or not set(ids) <= {c.id for c in dataset.cases}:
        raise ValueError("Duplicate or unknown conversation observations")
    by_id = {o["case_id"]: o for o in observations}
    cases = []
    for case in dataset.cases:
        checks = []
        def check(name, value):
            checks.append({"name": name, "status": "pass" if value else "fail"})
        observed = by_id.get(case.id)
        check("present", observed is not None)
        if observed:
            variants = observed["variants"]
            check("variants", [v["variant_id"] for v in variants] == [v.id for v in case.variants])
            if [v["variant_id"] for v in variants] == [v.id for v in case.variants]:
                for variant, observation in zip(case.variants, variants):
                    check(variant.id+".turn_count", len(variant.turns) == len(observation["turns"]))
                    for i, (turn, obs) in enumerate(zip(variant.turns, observation["turns"])):
                        exp = turn.expected
                        manifest, records = gold[(case.id, variant.id, i)]
                        prefix = f"{variant.id}.{i+1}."
                        for name in ("status", "mode", "response_status", "context_targets", "context_item", "pending", "decision", "effective_targets", "effective_item"):
                            check(prefix+name, obs[name] == getattr(exp, name))
                        check(prefix+"generation", obs["generation"] == (manifest.generation_id if exp.generation_present else None))
                        check(prefix+"exact_answer", obs["text"] == expected_text(exp, manifest, records))
                        citations = [c.model_dump() for c in expected_citations(manifest, records)]
                        check(prefix+"original_citations", obs["citations"] == citations)
                        check(prefix+"calls", Counts.model_validate(obs["calls"]) == exp.calls)
                        scopes = [{k: v for k, v in s.items() if k != "generation_id"} for s in obs["scopes"]]
                        sort = lambda values: sorted(values, key=lambda s: (s["restaurant_id"], s["document_type"] or ""))
                        check(prefix+"scopes", sort(scopes) == sort([s.model_dump() for s in exp.scopes])
                              and all(s["generation_id"] == manifest.generation_id for s in obs["scopes"]))
                        for name in ("original_memory", "private_state", "candidates_cleared"):
                            check(prefix+name, obs[name] is True)
        cases.append({"case_id": case.id, "passed": all(c["status"] == "pass" for c in checks), "checks": checks})
    return {"mode": "offline_regression", "dependencies": "simulated_dependencies", "expected_cases": 24,
            "observed_cases": len(observations), "passed": all(c["passed"] for c in cases),
            "measured_checks": sum(len(c["checks"]) for c in cases), "cases": cases}


def write_report(report, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    lines = ["# Offline document conversation regression", "", "Providers are simulated; live accuracy, ranking, latency and cost are unmeasured.",
             "", f"Passed: {report['passed']}; conversations: {report['observed_cases']}/24; checks: {report['measured_checks']}.",
             "", "| Case | Result | Failed checks |", "| --- | --- | --- |"]
    for case in report["cases"]:
        failures = ", ".join(c["name"] for c in case["checks"] if c["status"] == "fail")
        lines.append(f"| {case['case_id']} | {'pass' if case['passed'] else 'fail'} | {failures or 'none'} |")
    path.with_suffix(".md").write_text("\n".join(lines)+"\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", required=True)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output", type=Path, default=API_ROOT/".generated/evaluation/document-followups.json")
    args = parser.parse_args(argv)
    try:
        dataset = load_dataset(args.dataset)
        gold = compile_dataset(dataset)
        report = evaluate(dataset, run_offline(dataset, gold), gold)
        write_report(report, args.output)
        print(f"Followups: {report['observed_cases']}/24 conversations; passed={report['passed']}; checks={report['measured_checks']}")
        return 0 if report["passed"] else 1
    except Exception as error:
        print(f"Followups evaluation failed (error_type={type(error).__name__})")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
