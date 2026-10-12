"""Pin an active generation, resolve trusted scope, and verify retrieved chunks."""
from __future__ import annotations
import json
import math
import re
import time
from pathlib import Path

from src.domain.document_rag import ChunkRecord, DocumentQuery, EvidenceIntegrityError, GenerationManifest, RestaurantEntry, RetrievedEvidence, canonical_text
from src.infrastructure.rag_observability import rag_span


def router_catalog() -> list[dict]:
    data = json.loads((Path(__file__).resolve().parents[2] / "domain" / "document_catalog.json").read_text(encoding="utf-8"))
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
        return DocumentQuery(query=question, clarification="Please choose one fictional restaurant for this document question.")
    scope = found[0] if found else None
    # A new explicit venue that is not in the catalog must never inherit prior scope.
    explicit_unknown = bool(re.search(r"\b(?:at|for|about|from)\s+[A-Z][\w-]*(?:\s+[A-Z][\w-]*)+", question)) if not found else False
    if not scope and approved_scope in {r.restaurant_id for r in manifest.restaurants} and is_followup(question) and not explicit_unknown:
        scope = approved_scope
    if not scope:
        names = ", ".join(r.aliases[0] if r.aliases else r.name for r in manifest.restaurants)
        return DocumentQuery(query=question, clarification=f"Which fictional restaurant's documents should I use: {names}?")
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
    def __init__(self, store, vectors, embeddings, *, active_key="rag/active.json", top_k=5, max_characters=9000):
        self.store, self.vectors, self.embeddings = store, vectors, embeddings
        self.active_key, self.top_k, self.max_characters = active_key, top_k, max_characters

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
        if manifest.generation_id != pointer.generation_id or manifest.config != self.embeddings.config:
            raise EvidenceIntegrityError("Active generation/model configuration mismatch")
        self.check_deadline(deadline, clock)
        self.vectors.validate_index()
        return manifest

    def retrieve(self, query: DocumentQuery, manifest: GenerationManifest, *, deadline=None, clock=time.monotonic,
                 max_pages=None) -> list[RetrievedEvidence]:
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
