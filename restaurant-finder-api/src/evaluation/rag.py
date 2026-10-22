"""Deterministic checks for the controlled extractive RAG contract; no live runner."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domain.document_rag import DocumentCitation, RetrievedEvidence, canonical_text

API_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = Path(__file__).parent / "datasets" / "document_rag.json"
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_CASES = 50
OutcomeStatus = Literal["answered", "clarify", "insufficient_evidence", "invalid_answer", "disabled", "unavailable"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Calls(StrictModel):
    embedding: int = Field(ge=0, le=10)
    retrieval: int = Field(ge=0, le=10)
    selector: int = Field(ge=0, le=10)
    rewrite: int = Field(ge=0, le=10)


class GoldQuote(StrictModel):
    document_id: str = Field(pattern=r"^[a-z0-9-]{1,128}$")
    version: str = Field(min_length=1, max_length=64)
    quote: str = Field(min_length=1, max_length=600)
    page: int | None = Field(default=None, ge=1, le=10)
    section: str | None = Field(default=None, min_length=1, max_length=300)
    line_start: int | None = Field(default=None, ge=1, le=100000)
    line_end: int | None = Field(default=None, ge=1, le=100000)

    @model_validator(mode="after")
    def location(self):
        if len(canonical_text(self.quote)) < 10:
            raise ValueError("Gold quote must express a fact, not just a price token")
        if self.page is not None:
            if any(v is not None for v in (self.section, self.line_start, self.line_end)):
                raise ValueError("Mixed gold locations")
        elif not self.section or self.line_start is None or self.line_end is None or self.line_end < self.line_start:
            raise ValueError("Missing gold location")
        return self


class Expectation(StrictModel):
    status: OutcomeStatus
    restaurant_id: str | None = Field(default=None, pattern=r"^demo-[a-z0-9-]+$")
    document_type: Literal["menu", "policy"] | None = None
    quotes: list[GoldQuote] = Field(default_factory=list, max_length=3)
    text: str | None = Field(default=None, min_length=1, max_length=15000)
    forbidden_phrases: list[str] = Field(default_factory=list, max_length=20)
    calls: Calls

    @model_validator(mode="after")
    def coherent(self):
        if self.status == "answered":
            if not self.quotes or not self.restaurant_id or self.text is not None:
                raise ValueError("Answered expectation needs source quotes")
        elif self.quotes or not self.text:
            raise ValueError("Non-answer expectation needs exact safe response and no quotes")
        if any(not phrase or len(phrase) > 300 for phrase in self.forbidden_phrases):
            raise ValueError("Invalid forbidden phrase")
        return self


class ScriptSelection(StrictModel):
    document_id: str = Field(pattern=r"^[a-z0-9-]{1,128}$")
    quote: str = Field(min_length=1, max_length=600)
    chunk_id_override: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class Script(StrictModel):
    status: Literal["answered", "insufficient_evidence"]
    selections: list[ScriptSelection] = Field(default_factory=list, max_length=3)
    rewrite: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def coherent(self):
        if (self.status == "answered") != bool(self.selections):
            raise ValueError("Script status/selection mismatch")
        return self


class Case(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_-]{1,64}$")
    category: str = Field(pattern=r"^[a-z0-9_-]{1,64}$")
    corpus: Literal["corpus.json", "corpus-v2.json"]
    question: str = Field(min_length=1, max_length=1000)
    approved_scope: str | None = Field(default=None, pattern=r"^demo-[a-z0-9-]+$")
    expected: Expectation
    simulation: Script


class Dataset(StrictModel):
    schema_version: Literal[1]
    name: Literal["fictional-document-rag"]
    cases: list[Case] = Field(min_length=14, max_length=MAX_CASES)

    @model_validator(mode="after")
    def unique(self):
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("Duplicate case IDs")
        return self


class Observation(StrictModel):
    case_id: str = Field(pattern=r"^[a-z0-9_-]{1,64}$")
    origin: Literal["offline_simulated", "manual", "recorded"]
    status: OutcomeStatus
    text: str = Field(max_length=15000)
    restaurant_id: str | None = Field(default=None, pattern=r"^demo-[a-z0-9-]+$")
    generation_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    citations: list[DocumentCitation] = Field(default_factory=list, max_length=3)
    calls: Calls | None = None
    query_document_type: Literal["menu", "policy"] | None = None
    evidence: list[RetrievedEvidence] | None = Field(default=None, max_length=10)


class Observations(StrictModel):
    schema_version: Literal[1]
    observations: list[Observation] = Field(min_length=1, max_length=MAX_CASES)

    @model_validator(mode="after")
    def unique(self):
        if len({o.case_id for o in self.observations}) != len(self.observations):
            raise ValueError("Duplicate observation IDs")
        return self


def read_json(path):
    with Path(path).open("rb") as file:
        data = file.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("Input exceeds 2 MiB")
    def invalid_constant(_value):
        raise ValueError("Nonfinite JSON number")
    return json.loads(data.decode("utf-8"), parse_constant=invalid_constant)


def load_dataset(path=DATASET_PATH):
    return Dataset.model_validate(read_json(path))


def compile_dataset(dataset):
    """Ground human-written expectations in real locally parsed source records."""
    from src.application.document_rag.ingestion import prepare_generation

    manifests = {name: prepare_generation(API_ROOT / "sample_documents" / name)[0]
                 for name in sorted({case.corpus for case in dataset.cases})}
    grounded = {}
    for case in dataset.cases:
        manifest = manifests[case.corpus]
        restaurants = {r.restaurant_id for r in manifest.restaurants}
        if case.approved_scope and case.approved_scope not in restaurants:
            raise ValueError("Unknown approved scope")
        if case.expected.restaurant_id and case.expected.restaurant_id not in restaurants:
            raise ValueError("Unknown expected restaurant")
        quotes = []
        for gold in case.expected.quotes:
            matches = [chunk for chunk in manifest.chunks if chunk.document_id == gold.document_id
                       and chunk.restaurant_id == case.expected.restaurant_id and chunk.version == gold.version
                       and all(getattr(chunk, name) == getattr(gold, name)
                               for name in ("page", "section", "line_start", "line_end"))
                       and canonical_text(gold.quote) in chunk.text]
            if len(matches) != 1 or any(phrase.casefold() in gold.quote.casefold() for phrase in case.expected.forbidden_phrases):
                raise ValueError("Gold quote is not uniquely grounded or contradicts exclusions")
            if case.expected.document_type and matches[0].document_type != case.expected.document_type:
                raise ValueError("Gold quote has wrong document type")
            quotes.append((gold, matches[0]))
        grounded[case.id] = (manifest, quotes)
    return grounded


def escaped(text):
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", html.escape(canonical_text(text), quote=True))


def expected_answer(case, manifest, quotes):
    """Independent expected rendering; never calls the production renderer."""
    if case.expected.status != "answered":
        return case.expected.text
    names = {r.restaurant_id: r.name for r in manifest.restaurants}
    lines = ["According to the fictional demo documents:"]
    for index, (gold, chunk) in enumerate(quotes, 1):
        location = f"page {chunk.page}" if chunk.page else f"section {chunk.section}, lines {chunk.line_start}-{chunk.line_end}"
        provenance = f"{names[chunk.restaurant_id]}; {chunk.document_id}; {location}; version {chunk.version}; generation {manifest.generation_id[:12]}"
        lines.extend(["", f'> "{escaped(gold.quote)}"', "", f"Source: Source {index} — {escaped(provenance)}"])
    return "\n".join(lines)


def expected_citations(manifest, quotes):
    sources = {source.document_id: source for source in manifest.sources}
    result = []
    for index, (_, chunk) in enumerate(quotes, 1):
        source = sources[chunk.document_id]
        filename = Path(source.path).name
        result.append(DocumentCitation(label=f"Source {index}", generation_id=manifest.generation_id,
            document_id=chunk.document_id, chunk_id=chunk.chunk_id, source_hash=source.source_hash,
            format=Path(filename).suffix[1:], filename=filename, version=chunk.version,
            page=chunk.page, section=chunk.section, line_start=chunk.line_start, line_end=chunk.line_end))
    return result


def evaluate(dataset, observations, *, mode, grounded=None):
    if mode not in {"offline_regression", "imported_observations"}:
        raise ValueError("Unknown evaluation mode")
    observations = Observations.model_validate({"schema_version": 1, "observations": [o.model_dump() for o in observations]}).observations
    cases = {case.id: case for case in dataset.cases}
    if any(o.case_id not in cases for o in observations):
        raise ValueError("Unknown observation case")
    if mode == "offline_regression" and any(o.origin != "offline_simulated" for o in observations):
        raise ValueError("Offline mode requires simulated observations")
    grounded = grounded or compile_dataset(dataset)
    results = []
    for observation in observations:
        case = cases[observation.case_id]
        manifest, quotes = grounded[case.id]
        gold_citations = expected_citations(manifest, quotes)
        checks = {}

        def check(name, condition):
            checks[name] = "unmeasured" if condition is None else "pass" if condition else "fail"

        check("status", observation.status == case.expected.status)
        check("restaurant", observation.restaurant_id == case.expected.restaurant_id)
        check("generation", observation.generation_id == manifest.generation_id)
        check("answer_text", observation.text == expected_answer(case, manifest, quotes))
        check("excluded_claims", not any(phrase.casefold() in observation.text.casefold() for phrase in case.expected.forbidden_phrases))
        check("citation_count", len(observation.citations) == len(gold_citations))
        for field in DocumentCitation.model_fields:
            check("citation_" + field, len(observation.citations) == len(gold_citations) and all(
                getattr(actual, field) == getattr(gold, field) for actual, gold in zip(observation.citations, gold_citations)))
        check("calls", None if observation.calls is None else observation.calls == case.expected.calls)
        check("query_document_type", None if observation.calls is None else observation.query_document_type == case.expected.document_type)
        if observation.evidence is None:
            check("evidence_integrity", None)
            check("selected_evidence", None)
        else:
            references = {chunk.chunk_id: chunk for chunk in manifest.chunks}
            names = {r.restaurant_id: r.name for r in manifest.restaurants}
            def verified(item):
                ref = references.get(item.chunk_id)
                return (ref is not None and item.generation_id == manifest.generation_id
                        and item.restaurant_id == case.expected.restaurant_id
                        and (case.expected.document_type is None or item.document_type == case.expected.document_type)
                        and item.restaurant_name == names.get(item.restaurant_id)
                        and item.model_dump(exclude={"generation_id", "distance", "restaurant_name"}) == ref.model_dump(exclude={"key"}))
            check("evidence_integrity", len({e.chunk_id for e in observation.evidence}) == len(observation.evidence)
                  and all(verified(item) for item in observation.evidence))
            check("selected_evidence", all(c.chunk_id in {e.chunk_id for e in observation.evidence} for c in observation.citations))
        if mode == "offline_regression" and any(value == "unmeasured" for value in checks.values()):
            check("offline_measurements_complete", False)
        results.append({"case_id": case.id, "category": case.category, "declared_origin": observation.origin,
                        "passed": "fail" not in checks.values(), "checks": checks,
                        "expected_status": case.expected.status, "observed_status": observation.status,
                        "expected_documents": [gold.document_id for gold in gold_citations],
                        "observed_documents": [citation.document_id for citation in observation.citations]})
    missing = sorted(set(cases) - {o.case_id for o in observations})
    failed = sum(not row["passed"] for row in results)
    return {"schema_version": 1, "dataset": dataset.name, "mode": mode,
            "origin_verification": "simulated_dependencies" if mode == "offline_regression" else "imported_unverified",
            "complete": not missing, "passed": not missing and failed == 0,
            "dataset_cases": len(cases), "observed_cases": len(results), "failed_cases": failed,
            "missing_cases": missing, "measured_checks": sum(v != "unmeasured" for r in results for v in r["checks"].values()),
            "unmeasured_checks": sum(v == "unmeasured" for r in results for v in r["checks"].values()),
            "limitations": ["Offline simulations do not measure Jev/Haiku/Titan quality or semantic vector ranking.",
                            "Exact expected text checks the controlled extractive contract, not general paraphrase quality.",
                            "Imported observation origins are declared by the caller and are not authenticated."],
            "cases": results}


def summary(report):
    lines = ["# Document RAG evaluation", "", f"Mode: `{report['mode']}`; origin: `{report['origin_verification']}`.",
             f"Coverage: {report['observed_cases']}/{report['dataset_cases']}; complete: {report['complete']}; passed: {report['passed']}.",
             f"Failed cases: {report['failed_cases']}; unmeasured checks: {report['unmeasured_checks']}.", "",
             "| Case | Result | Failed/unmeasured checks |", "| --- | --- | --- |"]
    for row in report["cases"]:
        details = ", ".join(f"{key}: {value}" for key, value in row["checks"].items() if value != "pass") or "All measured checks passed"
        lines.append(f"| {row['case_id']} | {'PASS' if row['passed'] else 'FAIL'} | {details} |")
    if report["missing_cases"]:
        lines.extend(["", "Missing cases: " + ", ".join(report["missing_cases"])])
    lines.extend(["", *["- " + limit for limit in report["limitations"]], ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline", action="store_true")
    mode.add_argument("--observations", type=Path)
    mode.add_argument("--list-cases", action="store_true")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output", type=Path, default=Path(".generated/evaluation/document-rag.json"))
    args = parser.parse_args(argv)
    try:
        dataset = load_dataset(args.dataset)
        if args.list_cases:
            for case in dataset.cases:
                print(f"{case.id}: {case.question}")
            return 0
        grounded = compile_dataset(dataset)
        if args.offline:
            from src.evaluation.rag_offline import run_offline
            observations = run_offline(dataset, grounded)
            evaluation_mode = "offline_regression"
        else:
            observations = Observations.model_validate(read_json(args.observations)).observations
            evaluation_mode = "imported_observations"
        report = evaluate(dataset, observations, mode=evaluation_mode, grounded=grounded)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        rendered = summary(report)
        args.output.with_suffix(".md").write_text(rendered, encoding="utf-8")
        print(rendered)
        return 0 if report["passed"] else 1
    except Exception as error:
        # Do not echo input/provider payloads, paths, headers or validation values.
        print(f"Document RAG evaluation failed (error_type={type(error).__name__}).")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
