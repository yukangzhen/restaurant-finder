"""Pin an active generation, resolve trusted scope, and verify retrieved chunks."""
from __future__ import annotations
import json
import math
import re
import time
from pathlib import Path
from dataclasses import dataclass

from src.domain.document_rag import ChunkRecord, DocumentQuery, EvidenceIntegrityError, GenerationManifest, RestaurantEntry, RetrievedEvidence, canonical_text, generation_config
from src.infrastructure.rag_observability import rag_span
from src.application.document_rag.ranking import ALGORITHM_VERSION, FusedCandidate, KeywordCandidate, keyword_rank, reciprocal_rank_fusion, validate_top_k


@dataclass(frozen=True)
class HybridDiagnostics:
    """Private observations for injected offline checks; never part of graph state."""
    vector_keys: tuple[str, ...] = ()
    vector_distances: tuple[float, ...] = ()
    keyword: tuple[KeywordCandidate, ...] = ()
    fused: tuple[FusedCandidate, ...] = ()
    returned_keys: tuple[str, ...] = ()
    chunk_reads: int = 0


def router_catalog(*, include_real=None) -> list[dict]:
    data = json.loads((Path(__file__).resolve().parents[2] / "domain" / "document_catalog.json").read_text(encoding="utf-8"))
    if include_real is None:
        from src.config import settings
        include_real = settings.DOCUMENT_REAL_SOURCES_ENABLED
    if include_real:
        real = json.loads((Path(__file__).resolve().parents[2] / "domain" / "real_restaurant_catalog.json").read_text(encoding="utf-8"))
        data["restaurants"].extend(real["restaurants"])
    return [RestaurantEntry.model_validate(r).model_dump() for r in data["restaurants"]]


def is_followup(question: str) -> bool:
    return bool(re.search(r"\b(its|their|that restaurant|same restaurant|it|there)\b", question, re.I) or re.match(r"\s*(and|what about|how about)\b", question, re.I))


def resolve_query(question: str, manifest: GenerationManifest, approved_scope: str | None = None) -> DocumentQuery:
    question = canonical_text(question)[:1000]
    found = []
    name_spans = []
    for restaurant in manifest.restaurants:
        matches = [match for alias in [restaurant.name, *restaurant.aliases]
                   for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", question, re.I)]
        if matches:
            found.append(restaurant.restaurant_id)
            name_spans.extend(match.span() for match in matches)
    if len(found) > 1:
        label = "fictional restaurant" if all(r.fictional for r in manifest.restaurants) else "catalog restaurant"
        return DocumentQuery(query=question, clarification=f"Please choose one {label} for this document question.")
    scope = found[0] if found else None
    # A new explicit venue that is not in the catalog must never inherit prior scope.
    explicit_unknown = bool(re.search(r"\b(?:at|for|about|from)\s+[A-Z][\w-]*(?:\s+[A-Z][\w-]*)+", question)) if not found else False
    if not scope and approved_scope in {r.restaurant_id for r in manifest.restaurants} and is_followup(question) and not explicit_unknown:
        scope = approved_scope
    if not scope:
        names = ", ".join(r.aliases[0] if r.aliases else r.name for r in manifest.restaurants)
        label = "fictional restaurant" if all(r.fictional for r in manifest.restaurants) else "catalog restaurant"
        return DocumentQuery(query=question, clarification=f"Which {label}'s documents should I use: {names}?")
    # Names identify the venue, but their words must not imply document intent.
    # Mask all spans on a separate copy, preserving overlaps and the query itself.
    intent_characters = list(question)
    for start, end in name_spans:
        intent_characters[start:end] = [" "] * (end - start)
    intent_text = "".join(intent_characters)
    menu = bool(re.search(r"\b(menu|dish|pasta|price|cost|meal|ingredients)\b", intent_text, re.I))
    policy = bool(re.search(r"\b(policy|policies|cancellation|cancel|booking|reservation|fee|parking|allergies)\b", intent_text, re.I))
    return DocumentQuery(query=question, restaurant_id=scope, document_type="menu" if menu and not policy else "policy" if policy and not menu else None)


class DocumentRetriever:
    def __init__(self, store, vectors, embeddings, *, active_key="rag/active.json", top_k=5, max_characters=9000,
                 retrieval_mode="vector", diagnostics_observer=None):
        if retrieval_mode not in ("vector", "hybrid"):
            raise ValueError("Retrieval mode must be vector or hybrid")
        if retrieval_mode == "hybrid":
            validate_top_k(top_k)
            if type(max_characters) is not int or not 0 < max_characters <= 9000:
                raise ValueError("Invalid hybrid context bound")
        self.store, self.vectors, self.embeddings = store, vectors, embeddings
        self.active_key, self.top_k, self.max_characters = active_key, top_k, max_characters
        self.retrieval_mode, self.diagnostics_observer = retrieval_mode, diagnostics_observer

    @staticmethod
    def check_deadline(deadline, clock):
        if deadline is not None and clock() >= deadline:
            raise TimeoutError("Document deadline exhausted")

    def pin(self, *, deadline=None, clock=time.monotonic) -> GenerationManifest:
        self.check_deadline(deadline, clock)
        try:
            pointer, _ = self.store.active(self.active_key)
        except ValueError:
            raise EvidenceIntegrityError("Invalid active pointer") from None
        if pointer is None:
            raise ValueError("No active corpus")
        self.check_deadline(deadline, clock)
        try:
            data, _ = self.store.read_json(pointer.manifest_key)
            manifest = GenerationManifest.model_validate(data)
        except ValueError:
            raise EvidenceIntegrityError("Invalid generation manifest") from None
        if manifest.generation_id != pointer.generation_id or manifest.config != generation_config(manifest.schema_version, self.embeddings.config):
            raise EvidenceIntegrityError("Active generation/model configuration mismatch")
        self.check_deadline(deadline, clock)
        self.vectors.validate_index()
        return manifest

    def retrieve(self, query: DocumentQuery, manifest: GenerationManifest, *, deadline=None, clock=time.monotonic,
                 max_pages=None) -> list[RetrievedEvidence]:
        if self.retrieval_mode == "hybrid":
            return self._retrieve_hybrid(query, manifest, deadline=deadline, clock=clock, max_pages=max_pages)
        if query.clarification or query.restaurant_id not in {r.restaurant_id for r in manifest.restaurants}:
            raise ValueError("Retrieval requires an approved catalog scope")
        with rag_span("rag.embed", {"rag.embedding_model":self.embeddings.config.model_id}) as span:
            self.check_deadline(deadline, clock)
            vector = self.embeddings.embed(query.query)
            if span:
                span.set_attribute("rag.query_tokens", self.embeddings.tokens)
                span.set_attribute("rag.embedding_attempts", self.embeddings.attempts)
        with rag_span("rag.vector_query", {"rag.generation":manifest.generation_id, "rag.restaurant":query.restaurant_id, "rag.top_k":self.top_k}):
            self.check_deadline(deadline, clock)
            options = {"max_pages": max_pages} if max_pages is not None else {}
            hits = self.vectors.query(vector, manifest.generation_id, query.restaurant_id, query.document_type, self.top_k, **options)
        if len(hits) > self.top_k:
            raise EvidenceIntegrityError("Vector result exceeds requested bound")
        references = {f"{manifest.generation_id}:{c.chunk_id}": c for c in manifest.chunks}
        names = {r.restaurant_id: r.name for r in manifest.restaurants}
        evidence, seen, characters = [], set(), 0
        for hit in hits:
            if not isinstance(hit, dict):
                raise EvidenceIntegrityError("Invalid vector hit")
            ref = references.get(hit.get("key"))
            if ref is None or ref.restaurant_id != query.restaurant_id or (query.document_type and ref.document_type != query.document_type):
                raise EvidenceIntegrityError("Retrieved vector is outside the pinned scope")
            if hit["key"] in seen:
                raise EvidenceIntegrityError("Duplicate retrieved vector")
            seen.add(hit["key"])
            expected = {"generation_id": manifest.generation_id, "chunk_id": ref.chunk_id, "document_id": ref.document_id,
                        "restaurant_id": ref.restaurant_id, "document_type": ref.document_type}
            if hit.get("metadata") != expected or isinstance(hit.get("distance"), bool) or not isinstance(hit.get("distance"), (int, float)) or not math.isfinite(hit["distance"]):
                raise EvidenceIntegrityError("Retrieved vector metadata/distance is invalid")
            self.check_deadline(deadline, clock)
            try:
                data, _ = self.store.read_json(ref.key)
                chunk = ChunkRecord.model_validate(data)
            except ValueError:
                raise EvidenceIntegrityError("Invalid retrieved chunk") from None
            if chunk.model_dump() != ref.model_dump(exclude={"key"}):
                raise EvidenceIntegrityError("Retrieved source text/location/hash is inconsistent")
            if characters + len(chunk.text) > self.max_characters:
                continue  # Keep whole passages; never truncate their records.
            characters += len(chunk.text)
            evidence.append(RetrievedEvidence(**chunk.model_dump(), generation_id=manifest.generation_id,
                                             distance=hit["distance"], restaurant_name=names[chunk.restaurant_id]))
        return evidence

    def _retrieve_hybrid(self, query, manifest, *, deadline, clock, max_pages):
        guard = lambda: self.check_deadline(deadline, clock)
        guard()
        validate_top_k(self.top_k)
        if max_pages is not None and (type(max_pages) is not int or max_pages != 1):
            raise ValueError("Hybrid retrieval permits one vector page")
        try:
            manifest = GenerationManifest.model_validate(manifest.model_dump())
            query = DocumentQuery.model_validate(query.model_dump())
        except (ValueError, TypeError, AttributeError):
            raise EvidenceIntegrityError("Invalid hybrid retrieval contract") from None
        if manifest.config != generation_config(manifest.schema_version, self.embeddings.config):
            raise EvidenceIntegrityError("Generation/model configuration mismatch")
        if query.clarification or query.restaurant_id not in {r.restaurant_id for r in manifest.restaurants}:
            raise ValueError("Retrieval requires an approved catalog scope")
        pool = [c for c in manifest.chunks if c.restaurant_id == query.restaurant_id
                and (query.document_type is None or c.document_type == query.document_type)]
        if not pool:
            if self.diagnostics_observer:
                self.diagnostics_observer(HybridDiagnostics())
            return []
        attributes = {"rag.retrieval_mode": "hybrid", "rag.ranking_algorithm": ALGORITHM_VERSION,
                      "rag.generation": manifest.generation_id, "rag.restaurant": query.restaurant_id,
                      "rag.top_k": self.top_k}
        with rag_span("rag.keyword_rank", attributes) as span:
            from src.application.document_rag.native_menu import native_lookup_query
            keywords = keyword_rank(native_lookup_query(query, manifest), [(f"{manifest.generation_id}:{c.chunk_id}", c.text) for c in pool],
                                    top_k=self.top_k, guard=guard)
            if span:
                span.set_attribute("rag.keyword_candidates", len(keywords))
        with rag_span("rag.embed", {"rag.embedding_model": self.embeddings.config.model_id}) as span:
            guard()
            vector = self.embeddings.embed(query.query)
            guard()
            if span:
                span.set_attribute("rag.query_tokens", self.embeddings.tokens)
                span.set_attribute("rag.embedding_attempts", self.embeddings.attempts)
        with rag_span("rag.vector_query", attributes):
            guard()
            hits = self.vectors.query(vector, manifest.generation_id, query.restaurant_id, query.document_type,
                                      self.top_k, max_pages=1)
            guard()
        if not isinstance(hits, list) or len(hits) > self.top_k:
            raise EvidenceIntegrityError("Invalid vector result bound")
        references = {f"{manifest.generation_id}:{c.chunk_id}": c for c in pool}
        distances = {}
        for hit in hits:
            guard()
            if not isinstance(hit, dict) or not isinstance(hit.get("key"), str):
                raise EvidenceIntegrityError("Invalid vector hit")
            key = hit["key"]
            ref = references.get(key)
            if ref is None or key in distances:
                raise EvidenceIntegrityError("Vector scope or uniqueness violation")
            expected = {"generation_id": manifest.generation_id, "chunk_id": ref.chunk_id,
                        "document_id": ref.document_id, "restaurant_id": ref.restaurant_id,
                        "document_type": ref.document_type}
            distance = hit.get("distance")
            if hit.get("metadata") != expected or isinstance(distance, bool) or not isinstance(distance, (int, float)) or not math.isfinite(distance):
                raise EvidenceIntegrityError("Invalid vector metadata/distance")
            distances[key] = distance
        vector_keys = tuple(sorted(distances, key=lambda key: (distances[key], key)))
        # Every union member is verified, including candidates later excluded by rank/budget.
        chunks = {}
        for key in sorted(set(vector_keys) | {c.key for c in keywords}):
            guard()
            ref = references[key]
            try:
                data, _ = self.store.read_json(ref.key)
                chunk = ChunkRecord.model_validate(data)
            except (ValueError, TypeError):
                raise EvidenceIntegrityError("Invalid retrieved chunk") from None
            guard()
            if chunk.model_dump() != ref.model_dump(exclude={"key"}):
                raise EvidenceIntegrityError("Retrieved source text/location/hash is inconsistent")
            chunks[key] = chunk
        with rag_span("rag.fuse", attributes) as span:
            fused = reciprocal_rank_fusion(vector_keys, [c.key for c in keywords], top_k=self.top_k, guard=guard)
            names = {r.restaurant_id: r.name for r in manifest.restaurants}
            evidence, returned, characters = [], [], 0
            for candidate in fused[:self.top_k]:
                guard()
                chunk = chunks[candidate.key]
                if characters + len(chunk.text) > self.max_characters:
                    continue
                characters += len(chunk.text)
                evidence.append(RetrievedEvidence(**chunk.model_dump(), generation_id=manifest.generation_id,
                                                 distance=distances.get(candidate.key), restaurant_name=names[chunk.restaurant_id]))
                returned.append(candidate.key)
            if span:
                for name, count in {"vector_candidates": len(vector_keys), "keyword_candidates": len(keywords),
                                    "candidate_union": len(chunks), "candidate_overlap": len(set(vector_keys) & {c.key for c in keywords}),
                                    "passages": len(evidence), "context_characters": characters}.items():
                    span.set_attribute("rag." + name, count)
            guard()
            if self.diagnostics_observer:
                self.diagnostics_observer(HybridDiagnostics(vector_keys, tuple(distances[k] for k in vector_keys),
                    keywords, fused, tuple(returned), len(chunks)))
        return evidence
