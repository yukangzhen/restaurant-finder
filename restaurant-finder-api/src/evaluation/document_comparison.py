"""Offline comparison regression: real workflow, simulated providers, independent gold."""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
from contextlib import ExitStack
from pathlib import Path
from typing import Literal
from unittest.mock import patch

from pydantic import Field, model_validator

from src.domain.document_rag import DocumentCitation, RetrievedEvidence
from src.evaluation.rag import API_ROOT, GoldQuote, Script, StrictModel, expected_citations, escaped, read_json
from src.evaluation.rag_offline import MemoryStore, NoTelemetry, ScriptedSelector, SimulatedEmbeddings, SimulatedVectors, cloud_clients_forbidden

DATASET_PATH = Path(__file__).parent / "datasets" / "document_comparison.json"
Status = Literal["answered", "partial", "clarify", "insufficient_evidence", "unavailable", "invalid_answer", "disabled"]


class Calls(StrictModel):
    pin: int = Field(ge=0, le=1)
    embedding: int = Field(ge=0, le=2)
    retrieval: int = Field(ge=0, le=2)
    selector: int = Field(ge=0, le=2)
    rewrite: Literal[0] = 0
    chunk_reads: int = Field(ge=0, le=10)


class GoldRow(StrictModel):
    restaurant_id: str = Field(pattern=r"^demo-[a-z0-9-]+$")
    status: Literal["supported", "missing", "unavailable", "invalid"]
    quote: GoldQuote | None = None
    amount: str | None = Field(default=None, pattern=r"^[0-9]{1,8}(?:\.[0-9]{1,2})?$")
    unit: Literal["serving", "bowl", "piece"] | None = None

    @model_validator(mode="after")
    def coherent(self):
        if (self.status == "supported") != (self.quote is not None):
            raise ValueError("Gold row evidence/status mismatch")
        if (self.amount is None) != (self.unit is None) or (self.status != "supported" and self.amount is not None):
            raise ValueError("Gold price/status mismatch")
        return self


class Expectation(StrictModel):
    status: Status
    item: str | None = Field(default=None, min_length=1, max_length=80)
    rows: list[GoldRow] = Field(default_factory=list, max_length=2)
    difference: str | None = Field(default=None, pattern=r"^[0-9]{1,8}(?:\.[0-9]{1,2})?$")
    cheaper_id: str | None = Field(default=None, pattern=r"^demo-[a-z0-9-]+$")
    text: str | None = Field(default=None, min_length=1, max_length=15000)
    calls: Calls

    @model_validator(mode="after")
    def coherent(self):
        if self.status == "clarify":
            if self.rows or self.item or not self.text or self.difference or self.cheaper_id:
                raise ValueError("Clarification gold must have no facts")
        elif len(self.rows) != 2 or not self.item or len({r.restaurant_id for r in self.rows}) != 2:
            raise ValueError("Comparison gold needs two unique rows")
        if self.status in {"answered", "partial"} and self.text is not None:
            raise ValueError("Answer gold uses independently rendered records")
        if self.status not in {"answered", "partial", "clarify"} and not self.text:
            raise ValueError("Failure gold needs an exact safe response")
        return self


class WorkerScript(StrictModel):
    restaurant_id: str = Field(pattern=r"^demo-[a-z0-9-]+$")
    selector: Script
    fault: Literal["none", "provider_error"] = "none"


class Simulation(StrictModel):
    workers: list[WorkerScript] = Field(default_factory=list, max_length=2)
    pointer_changes: bool = False

    @model_validator(mode="after")
    def unique(self):
        if len({w.restaurant_id for w in self.workers}) != len(self.workers):
            raise ValueError("Duplicate simulated workers")
        return self


class Case(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_-]{1,64}$")
    corpus: Literal["corpus.json", "corpus-v2.json"]
    question: str = Field(min_length=1, max_length=1000)
    expected: Expectation
    simulation: Simulation


class Dataset(StrictModel):
    schema_version: Literal[1]
    name: Literal["fictional-document-comparison"]
    cases: list[Case] = Field(min_length=20, max_length=50)

    @model_validator(mode="after")
    def unique(self):
        if len({c.id for c in self.cases}) != len(self.cases):
            raise ValueError("Duplicate comparison case IDs")
        return self


class QueryScope(StrictModel):
    restaurant_id: str
    generation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    document_type: Literal["menu"]
    max_pages: Literal[1]


class Observation(StrictModel):
    case_id: str = Field(pattern=r"^[a-z0-9_-]{1,64}$")
    status: Status
    text: str = Field(max_length=15000)
    generation_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    rows: list[GoldRow] = Field(default_factory=list, max_length=2)
    difference: str | None = None
    cheaper_id: str | None = None
    retrieval_count: int = Field(ge=0, le=2)
    citations: list[DocumentCitation] = Field(default_factory=list, max_length=2)
    evidence: list[RetrievedEvidence] = Field(default_factory=list, max_length=10)
    scopes: list[QueryScope] = Field(default_factory=list, max_length=2)
    calls: Calls


def load_dataset(path=DATASET_PATH):
    return Dataset.model_validate(read_json(path))


def compile_dataset(dataset):
    from src.application.document_rag.ingestion import prepare_generation
    manifests = {name: prepare_generation(API_ROOT / "sample_documents" / name)[0]
                 for name in {case.corpus for case in dataset.cases}}
    grounded = {}
    for case in dataset.cases:
        manifest = manifests[case.corpus]
        ids = {r.restaurant_id for r in manifest.restaurants}
        quotes = []
        for row in case.expected.rows:
            if row.restaurant_id not in ids:
                raise ValueError("Unknown gold restaurant")
            if row.quote:
                gold = row.quote
                matches = [c for c in manifest.chunks if c.document_id == gold.document_id
                           and c.restaurant_id == row.restaurant_id and c.document_type == "menu"
                           and c.version == gold.version and gold.quote in c.text and all(
                               getattr(c, field) == getattr(gold, field) for field in
                               ("page", "section", "line_start", "line_end"))]
                if len(matches) != 1:
                    raise ValueError("Comparison gold is not uniquely grounded")
                quotes.append((gold, matches[0]))
        grounded[case.id] = (manifest, quotes)
    return grounded


class ComparisonHarness:
    """Test-only dependency bundle recording actual calls, never accessing gold."""
    def __init__(self, manifest, simulation):
        from src.application.document_rag.comparison_workflow import ComparisonDependencies
        from src.application.document_rag.retrieval import DocumentRetriever
        self.manifest, self.simulation = manifest, simulation
        self.pin_calls, self.chunk_reads, self.scopes, self.retrievers, self.selectors, self.results = 0, 0, [], [], [], []
        outer = self

        class Store(MemoryStore):
            def active(self, key):
                outer.pin_calls += 1
                pointer, etag = super().active(key)
                if simulation.pointer_changes:
                    self.pointer = self.pointer.model_copy(update={"generation_id": "f"*64,
                        "manifest_key": f"rag/generations/{'f'*64}/manifest.json"})
                return pointer, etag

            def read_json(self, key):
                if "/chunks/" in key:
                    outer.chunk_reads += 1
                return super().read_json(key)

        self.store = Store(manifest)

        class Vectors(SimulatedVectors):
            def __init__(self, rid):
                super().__init__(manifest)
                self.rid = rid

            def query(self, vector, generation_id, rid, document_type, top_k, *, max_pages=10):
                outer.scopes.append(QueryScope(restaurant_id=rid, generation_id=generation_id,
                                               document_type=document_type, max_pages=max_pages))
                script = next((w for w in simulation.workers if w.restaurant_id == rid), None)
                if script and script.fault == "provider_error":
                    self.attempts += 1
                    raise RuntimeError("SIMULATED_PRIVATE_PROVIDER_BODY")
                return super().query(vector, generation_id, rid, document_type, top_k)

        class RecordingRetriever(DocumentRetriever):
            def __init__(self, rid):
                super().__init__(outer.store, Vectors(rid), SimulatedEmbeddings(manifest.config))
                self.evidence = []

            def retrieve(self, *args, **kwargs):
                self.evidence = super().retrieve(*args, **kwargs)
                return self.evidence

        def retriever(rid):
            value = RecordingRetriever(rid)
            self.retrievers.append(value)
            return value

        def selector(rid):
            script = next(w.selector for w in simulation.workers if w.restaurant_id == rid)
            value = ScriptedSelector(script, manifest)
            self.selectors.append(value)
            return value

        self.dependencies = ComparisonDependencies(pin_factory=lambda: RecordingRetriever(None),
            retriever_factory=retriever, selector_factory=selector, result_observer=self.results.append)

    def counts(self):
        return Calls(pin=self.pin_calls, embedding=sum(r.embeddings.attempts for r in self.retrievers),
                     retrieval=sum(r.vectors.attempts for r in self.retrievers),
                     selector=sum(s.attempts for s in self.selectors), chunk_reads=self.chunk_reads)

    async def run(self, question):
        from langchain_core.messages import HumanMessage
        from src.application.document_rag.workflow import answer_document_question
        from src.config import settings
        with patch.object(settings, "DOCUMENT_RAG_ENABLED", True):
            return await answer_document_question({"messages": [HumanMessage(content=question)]}, {},
                                                  comparison_dependencies=self.dependencies)

    def observe(self, case_id, outcome):
        result = self.results[-1] if self.results else None
        rows = []
        if result:
            for row in result.rows:
                gold = None
                if row.selection:
                    e = row.evidence
                    gold = GoldQuote(document_id=e.document_id, version=e.version, quote=row.selection.quote,
                                     page=e.page, section=e.section, line_start=e.line_start, line_end=e.line_end)
                rows.append(GoldRow(restaurant_id=row.restaurant_id, status=row.status, quote=gold,
                    amount=str(row.price.amount) if row.price else None, unit=row.price.unit if row.price else None))
        return Observation(case_id=case_id, status=outcome.status, text=outcome.text, generation_id=outcome.generation_id,
            rows=rows, difference=str(result.difference) if result and result.difference is not None else None,
            cheaper_id=result.cheaper_id if result else None, retrieval_count=outcome.retrieval_count,
            citations=outcome.citations, scopes=self.scopes, calls=self.counts(),
            evidence=[e for r in self.retrievers for e in r.evidence])


def run_offline(dataset, grounded):
    with cloud_clients_forbidden(), ExitStack() as stack:
        stack.enter_context(patch("src.infrastructure.rag_observability.get_observability_manager", return_value=NoTelemetry()))
        from src.application.document_rag import workflow
        guard = stack.enter_context(patch.object(workflow, "structured_chain", side_effect=AssertionError("Live selector forbidden")))
        observations = []
        for case in dataset.cases:
            harness = ComparisonHarness(grounded[case.id][0], case.simulation)
            outcome = asyncio.run(harness.run(case.question))
            observations.append(harness.observe(case.id, outcome))
        if guard.called:
            raise AssertionError("Comparison attempted a live selector")
        return observations


def expected_text(case, manifest, quotes):
    """Independent rendering from handwritten gold; no production comparison helper."""
    exp = case.expected
    if exp.text:
        return exp.text
    names = {r.restaurant_id: r.name for r in manifest.restaurants}
    lines = ["Listed prices in the fictional demo documents:", "",
             f"| Restaurant | Listed {escaped(exp.item)} price | Evidence |", "| --- | --- | --- |"]
    supported, index = [], 0
    for row in exp.rows:
        if row.status == "supported":
            supported.append(row)
            index += 1
            value = f"RM{row.amount} per {row.unit}" if row.amount is not None else "Unsupported price format"
            label = f"Source {index}"
        else:
            value = "Not found in retrieved menu evidence" if row.status == "missing" else "Retrieval unavailable"
            label = "No verified source"
        lines.append(f"| {escaped(names[row.restaurant_id])} | {value} | {label} |")
    lines.extend(["", f"Document evidence: {len(supported)} of 2 restaurants supported."])
    if len(supported) < 2:
        lines.append("A price difference cannot be calculated because one restaurant has no verified result.")
    elif any(row.amount is None for row in supported):
        lines.append("A price difference cannot be calculated because a listed price format is unsupported.")
    elif supported[0].unit != supported[1].unit:
        lines.append("A price difference cannot be calculated because the listed serving units differ.")
    elif exp.difference == "0":
        lines.append(f"The listed prices are equal per {supported[0].unit}.")
    else:
        lines.append(f"{escaped(names[exp.cheaper_id])}'s listed price is RM{exp.difference} lower per {supported[0].unit}.")
    lines.extend(["", "According to the fictional demo documents:"])
    for index, (gold, chunk) in enumerate(quotes, 1):
        location = f"page {chunk.page}" if chunk.page else f"section {chunk.section}, lines {chunk.line_start}-{chunk.line_end}"
        provenance = f"{names[chunk.restaurant_id]}; {chunk.document_id}; {location}; version {chunk.version}; generation {manifest.generation_id[:12]}"
        lines.extend(["", f'> "{escaped(gold.quote)}"', "", f"Source: Source {index} — {escaped(provenance)}"])
    return "\n".join(lines)


def evaluate(dataset, observations, grounded):
    # Revalidate snapshots as well as typed inputs: model_copy can bypass validators.
    values = [Observation.model_validate(o.model_dump() if isinstance(o, Observation) else o) for o in observations]
    ids = [o.case_id for o in values]
    known = {case.id for case in dataset.cases}
    if len(ids) != len(set(ids)) or not set(ids) <= known:
        raise ValueError("Duplicate/unknown comparison observations")
    by_id = {o.case_id: o for o in values}
    reports = []
    for case in dataset.cases:
        checks = []
        def check(name, passed):
            checks.append({"name": name, "status": "pass" if passed else "fail"})
        observation = by_id.get(case.id)
        check("present", observation is not None)
        if observation:
            manifest, gold = grounded[case.id]
            final_gold = gold if case.expected.status in {"answered", "partial"} else []
            check("status", observation.status == case.expected.status)
            check("rows_and_relevant_records", observation.rows == case.expected.rows)
            check("generation", observation.generation_id == manifest.generation_id)
            check("exact_answer", observation.text == expected_text(case, manifest, final_gold))
            check("difference", observation.difference == case.expected.difference)
            check("cheaper_restaurant", observation.cheaper_id == case.expected.cheaper_id)
            check("original_citations", observation.citations == expected_citations(manifest, final_gold))
            check("measured_calls", observation.calls == case.expected.calls)
            check("started_retrievals", observation.retrieval_count == case.expected.calls.embedding)
            scopes = {(s.restaurant_id, s.generation_id, s.document_type, s.max_pages) for s in observation.scopes}
            expected_scopes = {(r.restaurant_id, manifest.generation_id, "menu", 1) for r in case.expected.rows}
            check("fixed_scopes", scopes == expected_scopes and len(observation.scopes) == len(expected_scopes))
            refs = {c.chunk_id: c for c in manifest.chunks}
            check("verified_evidence", len({e.chunk_id for e in observation.evidence}) == len(observation.evidence) and all(
                e.chunk_id in refs and e.generation_id == manifest.generation_id and all(
                getattr(e, field) == getattr(refs[e.chunk_id], field) for field in
                ("restaurant_id", "document_id", "document_type", "text", "text_hash", "version", "source_hash", "page", "section", "line_start", "line_end"))
                for e in observation.evidence))
            check("selected_evidence_present", all(c.chunk_id in {e.chunk_id for e in observation.evidence}
                                                   for c in observation.citations))
        reports.append({"case_id": case.id, "passed": all(c["status"] == "pass" for c in checks), "checks": checks})
    return {"schema_version": 1, "mode": "offline_regression", "origin_verification": "simulated_dependencies",
            "passed": all(r["passed"] for r in reports), "expected_cases": len(dataset.cases), "observed_cases": len(values),
            "missing_case_ids": sorted(known-set(ids)), "failed_case_ids": [r["case_id"] for r in reports if not r["passed"]],
            "measured_checks": sum(len(r["checks"]) for r in reports),
            "unmeasured": ["live_jev_routing", "live_selector_accuracy", "semantic_vector_ranking", "latency", "cost"],
            "cases": reports}


def write_report(report, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    lines = ["# Offline document comparison regression", "", "Providers are simulated; live accuracy, latency and cost are unmeasured.",
             "", f"Passed: {report['passed']}; cases: {report['observed_cases']}/{report['expected_cases']}; measured checks: {report['measured_checks']}.",
             "", "| Case | Result | Failed checks |", "| --- | --- | --- |"]
    for row in report["cases"]:
        failures = ", ".join(c["name"] for c in row["checks"] if c["status"] == "fail")
        lines.append(f"| {row['case_id']} | {'pass' if row['passed'] else 'fail'} | {failures or 'none'} |")
    path.with_suffix(".md").write_text("\n".join(lines)+"\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", required=True)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output", type=Path, default=API_ROOT / ".generated/evaluation/document-comparison.json")
    args = parser.parse_args(argv)
    try:
        dataset = load_dataset(args.dataset)
        grounded = compile_dataset(dataset)
        report = evaluate(dataset, run_offline(dataset, grounded), grounded)
        write_report(report, args.output)
        print(f"Comparison: {report['observed_cases']}/{report['expected_cases']} cases; passed={report['passed']}; checks={report['measured_checks']}")
        return 0 if report["passed"] else 1
    except Exception as error:
        print(f"Comparison evaluation failed (error_type={type(error).__name__})")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
