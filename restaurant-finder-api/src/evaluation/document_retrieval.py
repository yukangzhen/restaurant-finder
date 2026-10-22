"""Offline hybrid retrieval contracts; semantic candidates and providers are simulated."""
from __future__ import annotations

import argparse
import copy
import json
import math
from contextlib import ExitStack, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Any, Literal
from unittest.mock import AsyncMock, patch

from pydantic import Field, model_validator
from src.domain.document_rag import DocumentQuery
from src.evaluation.rag import API_ROOT, StrictModel, read_json
from src.evaluation.rag_offline import MemoryStore, NoTelemetry, SimulatedEmbeddings, cloud_clients_forbidden

DATASET_PATH = Path(__file__).parent / "datasets/document_retrieval.json"
H, S = "demo-harbor-pasta", "demo-sakura-table"
REQUIRED_VARIANTS = {
    "R01": ["main"], "R02": ["main"], "R03": ["main"], "R04": ["main"],
    "R05": ["forward", "reverse"], "R06": ["lower", "upper", "decomposed", "punctuation"],
    "R07": ["single", "repeated"], "R08": ["query_empty", "pool_empty", "scope_empty"],
    "R09": ["main"], "R10": ["main"], "R11": ["main"], "R12": ["main"],
    "R13": ["restricted", "unrestricted"], "R14": ["wrong_generation", "unknown_key", "bad_metadata"],
    "R15": ["duplicate", "nan", "infinity", "boolean", "excess", "malformed"],
    "R16": ["main"], "R17": ["main"], "R18": ["after_pin", "next_pin"],
    "R19": ["full", "budget"],
    "R20": ["expired", "keyword", "embedding_expiry", "vector_expiry", "read_expiry", "embedding_error", "vector_error", "cancelled"],
    "R21": ["default", "vector", "invalid_mode", "invalid_top_k", "invalid_boolean", "invalid_page"],
    "R22": ["empty", "all"], "R23": ["empty", "all"], "R24": ["approved", "block", "mask"],
}


class Hit(StrictModel):
    ref: str
    distance: float = .1


class Simulation(StrictModel):
    operation: Literal["retrieve", "config", "conversation"] = "retrieve"
    fixture: Literal["small", "wide", "silent", "empty_scope"] = "small"
    question: str = "mushroom"
    restaurant_id: str = H
    document_type: Literal["menu", "policy"] | None = "menu"
    hits: list[Hit] = Field(default_factory=list, max_length=10)
    retrieval_mode: Any = "hybrid"
    top_k: Any = 5
    max_characters: int = 9000
    max_pages: Any = None
    fault: str = ""
    corrupt_ref: str | None = None
    reverse: bool = False
    workflow: bool = False
    answer: dict = Field(default_factory=dict)
    conversation: str | None = None
    conversation_variant: str = "main"
    vector_response: Literal["empty", "all"] = "empty"


class Expected(StrictModel):
    error_type: str | None = None
    vector: list[list[str]] | None = None
    keyword: list[list[str]] | None = None
    fused: list[list[str]] | None = None
    returned: list[list[str]] | None = None
    retained: int | None = None
    embedding: int = 1
    retrieval: int = 1
    chunk_reads: int = 0
    pin: int = 1
    selector: int = 0
    status: str | None = None
    generation: Literal["v1", "v2"] = "v1"
    conversation: str | None = None
    conversation_variant: str = "main"
    conversation_reads: list[int] = Field(default_factory=list)
    vector_response: Literal["empty", "all"] = "empty"
    fused_from_ranks: bool = False
    distances: dict[str, float] = Field(default_factory=dict)
    read_until: str | None = None
    read_candidates: list[str] = Field(default_factory=list)
    restaurant_id: str = H
    document_type: Literal["menu", "policy"] | None = "menu"
    answer_ref: str | None = None
    answer_quote: str | None = None


class Variant(StrictModel):
    id: str
    simulation: Simulation
    expected: Expected


class Case(StrictModel):
    id: str
    variants: list[Variant]


class Dataset(StrictModel):
    schema_version: Literal[1]
    name: Literal["fictional-document-retrieval"]
    cases: list[Case]

    @model_validator(mode="after")
    def required_cases(self):
        if [c.id for c in self.cases] != list(REQUIRED_VARIANTS):
            raise ValueError("Required R01-R24 cases missing or reordered")
        for case in self.cases:
            if [v.id for v in case.variants] != REQUIRED_VARIANTS[case.id]:
                raise ValueError("Required retrieval variants missing or reordered")
        return self


def load_dataset(path=DATASET_PATH):
    return Dataset.model_validate(read_json(path))


@contextmanager
def offline_boundary():
    # These protections also apply when the CLI is invoked without the local helper.
    import socket
    connect, connect_ex = socket.socket.connect, socket.socket.connect_ex
    def local_pipe(original):
        def guarded(sock, address):
            # Windows asyncio uses a loopback socket pair for its internal wakeup pipe.
            if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
                return original(sock, address)
            raise AssertionError("Offline network forbidden")
        return guarded
    with cloud_clients_forbidden(), ExitStack() as stack:
        stack.enter_context(patch("socket.socket.connect", local_pipe(connect)))
        stack.enter_context(patch("socket.socket.connect_ex", local_pipe(connect_ex)))
        for target in ("socket.create_connection", "requests.sessions.Session.request", "httpx.Client.send", "httpx.AsyncClient.send"):
            stack.enter_context(patch(target, side_effect=AssertionError("Offline network forbidden")))
        telemetry = NoTelemetry()
        stack.enter_context(patch("src.infrastructure.rag_observability.get_observability_manager", return_value=telemetry))
        yield


def fixture(kind="small", version="v1"):
    """Synthetic documents use the real parser, hashes and manifest constructor."""
    from src.application.document_rag.ingestion import prepare_generation
    from src.application.document_rag.retrieval import router_catalog
    text = {
        "pasta": "Mushroom pasta - RM32 per serving. Contains wheat and milk.",
        "soup": "Tomato soup - RM12 per bowl. Vegan.",
        "cocoa": "Cocoa drink - RM9 per cup. Café special.",
        "cancel": "Cancellation less than 24 hours before booking incurs RM20 per booking.",
        "parking": "Valet parking is unconfirmed in this fictional document.",
        "sakura": "Mushroom pasta - RM36 per serving. Available at dinner only.",
    }
    if version == "v2":
        text["pasta"] = text["pasta"].replace("RM32", "RM99")
    groups = [("rank-menu", H, "menu", ["pasta", "soup", "cocoa"]),
              ("rank-policy", H, "policy", ["cancel", "parking"]),
              ("rank-sakura", S, "menu", ["sakura"])]
    if kind == "wide":
        text = {f"w{i:02}": ("lexicalneedle " if i < 5 else "vectorneedle ") + f"record {i:02} " + "z"*1000
                for i in range(48)}
        groups = [("rank-menu", H, "menu", list(text))]
    elif kind == "silent":
        text = {"!!!": "..."}
        groups = [("rank-menu", H, "menu", ["!!!"])]
    elif kind == "empty_scope":
        groups = [("rank-sakura", S, "menu", ["sakura"])]
    with TemporaryDirectory(prefix="retrieval-fixture-") as temp:
        root = Path(temp)
        specs = []
        for document_id, rid, doc_type, refs in groups:
            path = document_id + ".md"
            (root/path).write_text("\n\n".join("## "+ref+"\n\n"+text[ref] for ref in refs)+"\n", encoding="utf-8")
            specs.append(dict(document_id=document_id, restaurant_id=rid, document_type=doc_type, path=path, version=version))
        (root/"corpus.json").write_text(json.dumps(dict(fictional=True, restaurants=router_catalog(), documents=specs)), encoding="utf-8")
        manifest, _ = prepare_generation(root/"corpus.json")
    refs = {("silent" if c.section == "!!!" else c.section): c for c in manifest.chunks}
    return manifest, refs


class ObservedStore(MemoryStore):
    def __init__(self, manifest):
        super().__init__(manifest)
        self.reads, self.pins = [], 0
        self.corrupt_key = None
        self.expire = lambda: None
        self.next_pointer = None

    def active(self, key):
        self.pins += 1
        pointer, etag = super().active(key)
        if self.next_pointer:
            self.pointer, self.next_pointer = self.next_pointer, None
        return pointer, etag

    def read_json(self, key):
        value = super().read_json(key)
        if "/chunks/" in key:
            self.reads.append(key)
            self.expire()
            if key == self.corrupt_key:
                value[0]["text"] += " tampered"
        return value


def run_retrieval(simulation):
    """No Expected field enters dependency construction or invocation."""
    from src.application.document_rag.retrieval import DocumentRetriever
    sim = simulation
    manifest, refs = fixture(sim.fixture)
    store = ObservedStore(manifest)
    now, ticks = [0.0], [0]
    def clock():
        ticks[0] += 1
        if sim.fault == "keyword" and ticks[0] >= 3:
            return 10.0
        if sim.fault == "cancelled" and ticks[0] >= 4:
            raise TimeoutError("Stopped worker")
        return now[0]
    if sim.fault == "expired":
        now[0] = 10.0
    embeddings = SimulatedEmbeddings(manifest.config)
    embed = embeddings.embed
    def embed_observed(text):
        value = embed(text)
        if sim.fault == "embedding_error":
            raise RuntimeError("PRIVATE_SIMULATED_PROVIDER_BODY")
        if sim.fault == "embedding_expiry":
            now[0] = 10.0
        return value
    embeddings.embed = embed_observed
    scopes = []
    class Vectors:
        attempts = 0
        def validate_index(self): pass
        def query(self, _vector, generation, rid, doc_type, top_k, **options):
            self.attempts += 1
            scopes.append(dict(generation=generation, restaurant_id=rid, document_type=doc_type, **options))
            if sim.fault == "vector_error":
                raise RuntimeError("PRIVATE_SIMULATED_PROVIDER_BODY")
            if sim.fault == "vector_expiry":
                now[0] = 10.0
            hits = []
            for scripted in sim.hits:
                ref = refs[scripted.ref]
                hits.append(dict(key=f"{generation}:{ref.chunk_id}", distance=scripted.distance, metadata={
                    "generation_id": generation, "chunk_id": ref.chunk_id, "document_id": ref.document_id,
                    "restaurant_id": ref.restaurant_id, "document_type": ref.document_type}))
            if sim.fault == "wrong_generation": hits[0]["key"] = "f"*64+":"+refs[sim.hits[0].ref].chunk_id
            if sim.fault == "unknown_key": hits[0]["key"] = generation+":"+"f"*64
            if sim.fault == "bad_metadata": hits[0]["metadata"]["document_id"] = "forged"
            if sim.fault == "duplicate": hits.append(copy.deepcopy(hits[0]))
            if sim.fault in ("nan", "infinity", "boolean"):
                hits[0]["distance"] = {"nan":float("nan"), "infinity":float("inf"), "boolean":True}[sim.fault]
            if sim.fault == "excess": hits = hits * 6
            if sim.fault == "malformed": return [None]
            return list(reversed(hits)) if sim.reverse else hits
    vectors = Vectors()
    diagnostics, error, evidence, outcome, selector_calls = [], None, [], None, 0
    try:
        options = dict(top_k=sim.top_k, max_characters=sim.max_characters, diagnostics_observer=diagnostics.append)
        if sim.retrieval_mode is not None:
            options["retrieval_mode"] = sim.retrieval_mode
        retriever = DocumentRetriever(store, vectors, embeddings, **options)
        if not sim.workflow:
            manifest = retriever.pin()
        if sim.fault in ("after_pin", "next_pin"):
            next_manifest, next_refs = fixture(sim.fixture, "v2")
            new_store = MemoryStore(next_manifest)
            store.data.update(new_store.data)
            store.pointer = new_store.pointer
            if sim.fault == "next_pin":
                manifest, refs = retriever.pin(), next_refs
        if sim.reverse:
            manifest = manifest.model_copy(update={"chunks":list(reversed(manifest.chunks))})
        if sim.corrupt_ref:
            store.corrupt_key = refs[sim.corrupt_ref].key
        if sim.fault == "read_expiry":
            store.expire = lambda: now.__setitem__(0, 10.0)
        query = DocumentQuery(query=sim.question, restaurant_id=sim.restaurant_id, document_type=sim.document_type)
        if sim.workflow:
            import asyncio
            from langchain_core.messages import HumanMessage
            from src.application.document_rag import workflow
            from src.config import settings
            ref = refs[sim.answer["ref"]]
            selector = SimpleNamespace(ainvoke=AsyncMock(return_value={"status":"answered", "selections":[
                {"chunk_id":ref.chunk_id, "quote":sim.answer["quote"]}]}))
            # Observe the real workflow's evidence instead of invoking retrieval twice.
            retrieve = retriever.retrieve
            def recorded(*args, **kwargs):
                nonlocal evidence
                evidence = retrieve(*args, **kwargs)
                return evidence
            retriever.retrieve = recorded
            with patch.object(settings, "DOCUMENT_RAG_ENABLED", True), patch.object(settings, "DOCUMENT_FOLLOWUPS_ENABLED", False):
                outcome = asyncio.run(workflow.answer_document_question(
                    {"messages":[HumanMessage(content=sim.question)]}, {}, retriever=retriever, answer_chain=selector))
            selector_calls = selector.ainvoke.await_count
        else:
            evidence = retriever.retrieve(query, manifest, deadline=10.0, clock=clock, max_pages=sim.max_pages)
    except Exception as caught:
        error = type(caught).__name__
    return dict(error_type=error, evidence=evidence, diagnostics=diagnostics, scopes=scopes, manifest=manifest, refs=refs,
                reads=store.reads, pin=store.pins, embedding=embeddings.attempts, retrieval=vectors.attempts,
                outcome=outcome, selector=selector_calls)


def run_config(sim):
    from src.config import Settings
    from src.application.document_rag.retrieval import DocumentRetriever
    error = None
    try:
        mode = sim.retrieval_mode
        values = {} if mode is None else {"RAG_RETRIEVAL_MODE": mode}
        Settings(_env_file=None, RAG_TOP_K=sim.top_k, **values)
        DocumentRetriever(None, None, None, top_k=sim.top_k, **({} if mode is None else {"retrieval_mode":mode}))
        if sim.max_pages is not None:
            return run_retrieval(sim)
    except Exception as caught:
        error = type(caught).__name__
    return dict(error_type=error, pin=0, embedding=0, retrieval=0, selector=0, reads=[], diagnostics=[], evidence=[], scopes=[])


def conversation_dataset(case_id, variant_id):
    from src.evaluation import document_followups as followups
    source = next(c for c in followups.load_dataset().cases if c.id == case_id)
    variant = next(v for v in source.variants if v.id == variant_id).model_copy(deep=True)
    return SimpleNamespace(cases=[source.model_copy(update={"variants":[variant]})])


def run_conversation(sim):
    """Reuse executed parent-graph fixtures; do not inspect their expected answers here."""
    from src.evaluation import document_followups as followups
    from src.application.document_rag import retrieval
    dataset = conversation_dataset(sim.conversation, sim.conversation_variant)
    gold = followups.compile_dataset(dataset)
    base = retrieval.DocumentRetriever
    diagnostics, modes = [], []
    class Hybrid(base):
        def __init__(self, *args, **kwargs):
            kwargs.update(retrieval_mode="hybrid", diagnostics_observer=diagnostics.append)
            super().__init__(*args, **kwargs)
            modes.append(self.retrieval_mode)
    def empty_vectors(self, _vector, _generation, _rid, _kind, _top_k):
        self.attempts += 1
        return []
    with ExitStack() as stack:
        stack.enter_context(patch.object(retrieval, "DocumentRetriever", Hybrid))
        if sim.vector_response == "empty":
            stack.enter_context(patch.object(followups.SimulatedVectors, "query", empty_vectors))
        observations = followups.run_offline(dataset, gold)
    return dict(conversations=observations, modes=modes, diagnostics=diagnostics)


def run_offline(dataset):
    observations = []
    with offline_boundary():
        for case in dataset.cases:
            variants = []
            for variant in case.variants:
                sim = variant.simulation
                run = {"retrieve":run_retrieval, "config":run_config, "conversation":run_conversation}[sim.operation]
                variants.append({"variant_id":variant.id, "result":run(sim)})
            observations.append({"case_id":case.id, "variants":variants})
    return observations


def _ordered(bands, refs, manifest):
    return [f"{manifest.generation_id}:{refs[name].chunk_id}" for band in bands
            for name in sorted(band, key=lambda name:refs[name].chunk_id)]


def score_retrieval(expected, obs, check):
    exp = expected
    check("error", obs["error_type"] == exp.error_type)
    for name in ("pin", "embedding", "retrieval", "selector"):
        check(name, obs[name] == getattr(exp, name))
    read_count = exp.chunk_reads
    if exp.read_until and "refs" in obs:
        ordered = sorted(exp.read_candidates, key=lambda ref:obs["refs"][ref].chunk_id)
        read_count = ordered.index(exp.read_until) + 1
    check("chunk_reads", len(obs["reads"]) == read_count and len(obs["reads"]) == len(set(obs["reads"])))
    if exp.error_type or "refs" not in obs:
        check("no_unverified_evidence", not obs["evidence"])
        return
    manifest, refs = obs["manifest"], obs["refs"]
    check("generation_version", all(s.version == exp.generation for s in manifest.sources))
    check("scope", all(s["generation"] == manifest.generation_id and s["restaurant_id"] == exp.restaurant_id
                       and s["document_type"] == exp.document_type for s in obs["scopes"]))
    if exp.fused is not None or exp.fused_from_ranks:
        check("diagnostic_present", len(obs["diagnostics"]) == 1)
        if len(obs["diagnostics"]) != 1:
            return
        diag = obs["diagnostics"][0]
        vector = _ordered(exp.vector or [], refs, manifest)
        keyword = _ordered(exp.keyword or [], refs, manifest)
        fused = _ordered(exp.fused or [], refs, manifest)
        if exp.fused_from_ranks:
            # Independent reference uses declared gold ranks, never observed rankings.
            weights = {key:sum(1/(60+values.index(key)+1) for values in (vector,keyword) if key in values)
                       for key in set(vector+keyword)}
            fused = sorted(weights, key=lambda key:(-weights[key],key))
        check("vector_order", list(diag.vector_keys) == vector)
        expected_distances = {manifest.generation_id+":"+refs[name].chunk_id:value for name,value in exp.distances.items()}
        check("vector_distances", dict(zip(diag.vector_keys, diag.vector_distances)) == expected_distances)
        check("keyword_order", [c.key for c in diag.keyword] == keyword)
        check("fusion_order", [c.key for c in diag.fused] == fused)
        check("finite_keyword_scores", all(math.isfinite(c.score) and c.score > 0 for c in diag.keyword))
        vr, kr = {k:i+1 for i,k in enumerate(vector)}, {k:i+1 for i,k in enumerate(keyword)}
        check("ranks_and_formula", all(c.vector_rank == vr.get(c.key) and c.keyword_rank == kr.get(c.key)
            and math.isclose(c.score, sum(1/(60+rank) for rank in (vr.get(c.key),kr.get(c.key)) if rank is not None),
                             rel_tol=1e-14) for c in diag.fused))
        check("union_verified", set(diag.vector_keys) | {c.key for c in diag.keyword} ==
              {manifest.generation_id+":"+key.rsplit("/",1)[-1].removesuffix(".json") for key in obs["reads"]})
        check("diagnostic_reads", diag.chunk_reads == exp.chunk_reads)
        check("union_bounds", len(diag.fused) <= 10)
        if exp.returned is not None:
            returned = _ordered(exp.returned, refs, manifest)
        else:
            returned = fused[:5]
        if exp.retained is not None:
            returned = returned[:exp.retained]
        check("returned_order", [manifest.generation_id+":"+e.chunk_id for e in obs["evidence"]] == returned
              and list(diag.returned_keys) == returned)
        distance_by_key = expected_distances
        check("distance_truth", all(e.distance == distance_by_key.get(manifest.generation_id+":"+e.chunk_id) for e in obs["evidence"]))
    chunks = {c.chunk_id:c for c in manifest.chunks}
    check("source_integrity", all(e.generation_id == manifest.generation_id and e.chunk_id in chunks and
        e.model_dump(exclude={"generation_id","distance","restaurant_name"}) ==
        chunks[e.chunk_id].model_dump(exclude={"key"}) for e in obs["evidence"]))
    check("evidence_bounds", len(obs["evidence"]) <= 5 and sum(len(e.text) for e in obs["evidence"]) <= 9000)
    if exp.status is not None:
        outcome = obs["outcome"]
        check("answer_status", outcome is not None and outcome.status == exp.status)
        check("original_citation", outcome is not None and (not outcome.citations if exp.status != "answered" else len(outcome.citations) == 1 and
            any(c.chunk_id == e.chunk_id and c.source_hash == e.source_hash and c.version == e.version and
                c.page == e.page and c.line_start == e.line_start and c.line_end == e.line_end
                and c.generation_id == e.generation_id for c in outcome.citations for e in obs["evidence"])))
        if exp.status == "answered":
            from src.evaluation.rag import GoldQuote, expected_answer, expected_citations
            if not exp.answer_ref or not exp.answer_quote:
                raise ValueError("Answered gold requires an independent quote and source")
            ref = refs[exp.answer_ref]
            record = GoldQuote(document_id=ref.document_id, version=ref.version, quote=exp.answer_quote,
                              page=ref.page, section=ref.section, line_start=ref.line_start, line_end=ref.line_end)
            gold = [(record,ref)]
            check("exact_answer", outcome.text == expected_answer(SimpleNamespace(expected=exp),manifest,gold))
            check("exact_original", outcome.citations == expected_citations(manifest,gold))


def score_conversation(expected, obs, check):
    from src.evaluation import document_followups as followups
    dataset = conversation_dataset(expected.conversation, expected.conversation_variant)
    variant = dataset.cases[0].variants[0]
    if len(variant.turns) != len(expected.conversation_reads):
        raise ValueError("Missing independent conversation read counts")
    for turn, reads in zip(variant.turns, expected.conversation_reads):
        turn.expected.calls.chunk_reads = reads
        for scope in turn.expected.scopes:
            scope.max_pages = 1
    gold = followups.compile_dataset(dataset)
    report = followups.evaluate(dataset, obs["conversations"], gold)
    for case in report["cases"]:
        for result in case["checks"]:
            check("conversation."+result["name"], result["status"] == "pass")
    check("all_retrievers_hybrid", bool(obs["modes"]) and set(obs["modes"]) == {"hybrid"})
    check("actual_hybrid_diagnostics", bool(obs["diagnostics"]))
    check("vector_response", all(not d.vector_keys for d in obs["diagnostics"])
          if expected.vector_response == "empty" else any(d.vector_keys for d in obs["diagnostics"]))
    check("union_read_bound", all(d.chunk_reads <= 10 for d in obs["diagnostics"]))


def evaluate(dataset, observations):
    ids = [o["case_id"] for o in observations]
    if len(ids) != len(set(ids)) or not set(ids) <= set(REQUIRED_VARIANTS):
        raise ValueError("Duplicate or unknown retrieval observation")
    indexed = {o["case_id"]:o for o in observations}
    rows = []
    for case in dataset.cases:
        checks = []
        def check(name, passed):
            checks.append({"name":name, "status":"pass" if passed else "fail"})
        obs = indexed.get(case.id)
        check("case_present", obs is not None)
        if obs:
            expected_ids = [v.id for v in case.variants]
            check("variants", [v["variant_id"] for v in obs["variants"]] == expected_ids)
            if [v["variant_id"] for v in obs["variants"]] == expected_ids:
                for variant, measured in zip(case.variants, obs["variants"]):
                    prefix = variant.id+"."
                    mark = lambda name, value:check(prefix+name, value)
                    if variant.simulation.operation == "conversation":
                        score_conversation(variant.expected, measured["result"], mark)
                    else:
                        score_retrieval(variant.expected, measured["result"], mark)
        rows.append({"case_id":case.id, "passed":all(c["status"] == "pass" for c in checks), "checks":checks})
    return dict(mode="offline_regression", dependencies="simulated_dependencies", expected_cases=24,
                observed_cases=len(observations), expected_variants=sum(len(c.variants) for c in dataset.cases),
                observed_variants=sum(len(c["variants"]) for c in observations),
                complete=len(observations)==24 and all(any(x["name"]=="variants" and x["status"]=="pass" for x in r["checks"]) for r in rows),
                passed=all(r["passed"] for r in rows), measured_checks=sum(len(r["checks"]) for r in rows), cases=rows,
                limitations=["Semantic candidates, models and services are simulated; live ranking quality, cost and latency are unmeasured."])


def write_report(report, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    lines = ["# Offline hybrid retrieval regression", "", "Mode: offline_regression; dependencies: simulated_dependencies.",
             "", f"Cases: {report['observed_cases']}/24; variants: {report['observed_variants']}/{report['expected_variants']}; passed: {report['passed']}.",
             "", "| Case | Result | Failed checks |", "| --- | --- | --- |"]
    for row in report["cases"]:
        failed = ", ".join(c["name"] for c in row["checks"] if c["status"]!="pass")
        lines.append(f"| {row['case_id']} | {'PASS' if row['passed'] else 'FAIL'} | {failed or 'none'} |")
    lines.extend(["", *report["limitations"]])
    output.with_suffix(".md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", required=True)
    parser.add_argument("--dataset",type=Path,default=DATASET_PATH)
    parser.add_argument("--output",type=Path,default=API_ROOT/".generated/evaluation/document-retrieval.json")
    args = parser.parse_args(argv)
    try:
        dataset = load_dataset(args.dataset)
        report = evaluate(dataset, run_offline(dataset))
        write_report(report,args.output)
        print(f"Retrieval: {report['observed_cases']}/24 cases; {report['observed_variants']} variants; passed={report['passed']}; checks={report['measured_checks']}")
        return 0 if report["passed"] and report["complete"] else 1
    except Exception as error:
        print(f"Retrieval evaluation failed (error_type={type(error).__name__})")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
