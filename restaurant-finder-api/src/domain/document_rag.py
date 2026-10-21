"""Validated contracts shared by ingestion and read-only document answering."""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import unicodedata
from importlib.metadata import version as package_version
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator
from src.domain.document_conversation import DocumentContextDraft


class EvidenceIntegrityError(ValueError):
    """Fixed-message provenance failure; distinct from provider unavailability."""


def canonical_text(text: str) -> str:
    """Stable whitespace/Unicode normalization; keep prices and negation intact."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def digest(value: bytes | str | dict | list) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def validate_vector(values: list[float], dimensions: int = 512) -> list[float]:
    if len(values) != dimensions or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("Embedding must contain exactly 512 finite numbers")
    try:
        values = [struct.unpack("f",struct.pack("f",float(v)))[0] for v in values]
    except (OverflowError, struct.error) as error:
        raise ValueError("Embedding value is outside float32 range") from error
    if not any(values):
        raise ValueError("Embedding must not be a zero vector")
    return values


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RestaurantEntry(Contract):
    restaurant_id: str = Field(pattern=r"^demo-[a-z0-9-]+$")
    name: str
    aliases: list[str] = Field(default_factory=list)
    fictional: bool = True
    city: str | None = None
    cuisine: str | None = None
    website: str | None = None


def public_source_url(value: str) -> str:
    parts = urlsplit(value)
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment
            or any(c.isspace() or not c.isprintable() or c in '\\<>"`[]()' for c in value)):
        raise ValueError("Source URL must be a public HTTPS URL without credentials or query data")
    return value


class SourceProvenance(Contract):
    kind: Literal["official_pdf", "booking_page_snapshot", "booking_page_pdf", "menu_page_pdf"]
    origin_url: str
    resolved_url: str
    website_url: str
    captured_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T.*(?:Z|[+]\d{2}:\d{2})$")
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def public_urls(self):
        for value in (self.origin_url, self.resolved_url, self.website_url):
            public_source_url(value)
        return self


class NativeMenuAnchor(Contract):
    item: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    page: int = Field(ge=1, le=12)
    start: str = Field(min_length=1, max_length=100)
    end: str = Field(min_length=1, max_length=100)
    price_position: Literal["after_title", "after_description"]
    charge_note: str | None = Field(default=None, min_length=1, max_length=300)


class NativeMenuProfile(Contract):
    """Reviewed native-text boundaries, never model-authored facts or prices."""
    records: list[NativeMenuAnchor] = Field(min_length=1, max_length=12)
    decorative_pages: list[int] = Field(default_factory=list, max_length=12)
    currency: Literal["MYR"] | None = None
    currency_source_url: str | None = None
    currency_source_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    currency_excerpt: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def consistent(self):
        proof = (self.currency_source_url, self.currency_source_sha256, self.currency_excerpt)
        if self.currency is not None:
            if not all(proof) or not re.search(r"\bRM\s*\d", self.currency_excerpt):
                raise ValueError("Currency requires reviewed explicit RM source evidence")
            public_source_url(self.currency_source_url)
        elif any(proof):
            raise ValueError("Currency proof requires an explicit currency")
        if len(set(self.decorative_pages)) != len(self.decorative_pages) or any(type(p) is not int or not 1 <= p <= 12 for p in self.decorative_pages):
            raise ValueError("Invalid decorative page list")
        if any(a.page in self.decorative_pages for a in self.records):
            raise ValueError("A menu record cannot be on a decorative page")
        return self


class DocumentSpec(Contract):
    document_id: str = Field(pattern=r"^[a-z0-9-]+$")
    restaurant_id: str
    path: str
    document_type: Literal["menu", "policy"]
    version: str = Field(min_length=1, max_length=64)
    provenance: SourceProvenance | None = None
    native_menu: NativeMenuProfile | None = None

    @model_validator(mode="after")
    def source_profile(self):
        if self.native_menu is not None and (self.document_type != "menu" or not self.path.lower().endswith(".pdf")
                or self.provenance is None or self.provenance.kind not in {"official_pdf", "menu_page_pdf"}):
            raise ValueError("Native menu profiles require an official or captured menu PDF")
        if self.provenance and ((self.provenance.kind in {"official_pdf", "booking_page_pdf", "menu_page_pdf"}) != self.path.lower().endswith(".pdf")):
            raise ValueError("Source provenance differs from original format")
        if self.provenance and self.provenance.kind == "booking_page_pdf" and self.document_type != "policy":
            raise ValueError("Booking-page PDFs must contain policy documents")
        if self.provenance and self.provenance.kind == "menu_page_pdf" and self.document_type != "menu":
            raise ValueError("Menu-page PDFs must contain menu documents")
        if self.native_menu and self.provenance.kind != "menu_page_pdf" and any(
                record.charge_note is None for record in self.native_menu.records):
            raise ValueError("Official native menu PDFs require a reviewed printed charge note")
        return self


class CorpusSpec(Contract):
    schema_version: Literal[1, 2] = 1
    fictional: bool
    restaurants: list[RestaurantEntry]
    documents: list[DocumentSpec]

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [r.restaurant_id for r in self.restaurants]
        docs = [d.document_id for d in self.documents]
        if len(ids) != len(set(ids)) or len(docs) != len(set(docs)):
            raise ValueError("Duplicate restaurant/document IDs")
        if any(d.restaurant_id not in ids for d in self.documents):
            raise ValueError("Unknown restaurant in document catalog")
        names = [canonical_text(n).casefold() for r in self.restaurants for n in [r.name, *r.aliases]]
        if len(names) != len(set(names)):
            raise ValueError("Ambiguous restaurant name/alias")
        if not self.documents or len(self.documents) > 6:
            raise ValueError("Corpus document count exceeds its schema bound")
        validate_catalog_schema(self.schema_version, self.restaurants, self.documents)
        if self.fictional != all(r.fictional for r in self.restaurants):
            raise ValueError("Corpus fictional flag differs from its venues")
        return self


def validate_catalog_schema(schema_version, restaurants, sources):
    by_id = {r.restaurant_id: r for r in restaurants}
    if len(by_id) != len(restaurants):
        raise ValueError("Duplicate restaurant IDs")
    names = [canonical_text(n).casefold() for r in restaurants for n in [r.name, *r.aliases]]
    if len(names) != len(set(names)):
        raise ValueError("Ambiguous restaurant name/alias")
    if not sources or len(sources) > 6:
        raise ValueError("Source count exceeds manifest schema bound")
    if schema_version == 1 and (any(not r.fictional or any((r.city, r.cuisine, r.website)) for r in restaurants)
                               or any(s.provenance or s.native_menu for s in sources)):
        raise ValueError("Real-source metadata requires manifest schema 2")
    for source in sources:
        venue = by_id.get(source.restaurant_id)
        if venue is None:
            raise ValueError("Unknown source venue")
        if not venue.fictional and (not venue.city or not venue.cuisine or not venue.website or source.provenance is None):
            raise ValueError("Real venues require location, cuisine, website and source provenance")
        if not venue.fictional:
            public_source_url(venue.website)
            if source.provenance.website_url != venue.website:
                raise ValueError("Source provenance belongs to another venue website")


def generation_fingerprint(config, restaurants, sources, schema_version=1):
    if schema_version == 1:
        # Preserve the exact published v1 fingerprint, including empty aliases.
        return {"config": config.model_dump(), "restaurants": [r.model_dump(include={"restaurant_id", "name", "aliases"}) for r in restaurants],
                "sources": sorted([[s.document_id, s.restaurant_id, s.document_type, s.version, s.source_hash] for s in sources])}
    return {"schema_version": 2, "config": config.model_dump(), "restaurants": [r.model_dump() for r in restaurants],
            "sources": [s.model_dump(exclude={"key"}) for s in sorted(sources, key=lambda s:s.document_id)]}


def document_description(manifest, restaurant_ids=None):
    venues = [r for r in manifest.restaurants if restaurant_ids is None or r.restaurant_id in restaurant_ids]
    return "fictional demo documents" if venues and all(r.fictional for r in venues) else "captured source documents"


class ExtractedUnit(Contract):
    text: str
    page: int | None = Field(default=None, ge=1, le=12)
    section: str | None = None
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def location(self):
        if self.page is None and (not self.section or not self.line_start or not self.line_end):
            raise ValueError("A page or section/line location is required")
        return self


class ChunkRecord(ExtractedUnit):
    chunk_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    document_id: str
    source_hash: str
    text_hash: str
    restaurant_id: str
    document_type: Literal["menu", "policy"]
    version: str


class RagConfig(Contract):
    schema_version: Literal[1] = 1
    extractor: str = Field(default_factory=lambda: f"pypdf-{package_version('pypdf')}-markdown-v1")
    chunker: str = "records-v1"
    model_id: Literal["amazon.titan-embed-text-v2:0"] = "amazon.titan-embed-text-v2:0"
    dimensions: Literal[512] = 512
    normalize: Literal[True] = True
    max_chunk_characters: Literal[1800] = 1800
    overlap_characters: Literal[200] = 200


def generation_config(schema_version, config=None):
    """Check source extraction versions separately from the fixed embedding model.

    Schema 1 keeps its published identity. Schema 2 additionally pins the native
    font decoder; readers must have the same decoder as the prepared originals.
    """
    config = config or RagConfig()
    if schema_version == 2:
        return config.model_copy(update={"extractor": f"pypdf-{package_version('pypdf')}-fonttools-{package_version('fonttools')}-markdown-v1"})
    return config


class ChunkReference(ChunkRecord):
    key: str


class SourceReference(DocumentSpec):
    source_hash: str
    key: str


class GenerationManifest(Contract):
    schema_version: Literal[1, 2] = 1
    generation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    config: RagConfig
    restaurants: list[RestaurantEntry]
    sources: list[SourceReference]
    chunks: list[ChunkReference] = Field(min_length=1, max_length=48)

    @model_validator(mode="after")
    def integrity(self):
        validate_catalog_schema(self.schema_version, self.restaurants, self.sources)
        restaurant_ids = {r.restaurant_id for r in self.restaurants}
        sources = {s.document_id: s for s in self.sources}
        if len(sources) != len(self.sources) or len({c.chunk_id for c in self.chunks}) != len(self.chunks):
            raise ValueError("Duplicate manifest IDs")
        root = f"rag/generations/{self.generation_id}/"
        for source in self.sources:
            if source.restaurant_id not in restaurant_ids or not source.key.startswith(root + "sources/") or ".." in source.key:
                raise ValueError("Invalid source reference")
            if source.provenance and source.provenance.content_sha256 != source.source_hash:
                raise ValueError("Source provenance hash differs from stored original")
        for chunk in self.chunks:
            source = sources.get(chunk.document_id)
            if (source is None or chunk.restaurant_id != source.restaurant_id or chunk.source_hash != source.source_hash
                or chunk.document_type != source.document_type or chunk.version != source.version
                or chunk.key != root + f"chunks/{chunk.chunk_id}.json"
                or chunk.text_hash != digest(chunk.text) or canonical_text(chunk.text) != chunk.text
                or len(chunk.text) > self.config.max_chunk_characters):
                raise ValueError("Invalid chunk reference")
            location = {k: getattr(chunk, k) for k in ("page", "section", "line_start", "line_end")}
            if chunk.chunk_id != digest([chunk.document_id, chunk.source_hash, location, chunk.text]):
                raise ValueError("Chunk ID does not match its content")
        fingerprint = generation_fingerprint(self.config, self.restaurants, self.sources, self.schema_version)
        if digest(fingerprint) != self.generation_id:
            raise ValueError("Generation fingerprint does not match")
        return self


class ActivePointer(Contract):
    schema_version: Literal[1] = 1
    generation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    manifest_key: str

    @model_validator(mode="after")
    def safe_key(self):
        if self.manifest_key != f"rag/generations/{self.generation_id}/manifest.json":
            raise ValueError("Invalid active manifest key")
        return self


class DocumentQuery(Contract):
    query: str = Field(min_length=1, max_length=1000)
    restaurant_id: str | None = None
    document_type: Literal["menu", "policy"] | None = None
    clarification: str | None = None


class RetrievedEvidence(ChunkRecord):
    generation_id: str
    distance: float | None = Field(default=None, strict=True, allow_inf_nan=False)
    restaurant_name: str


class QuoteSelection(Contract):
    chunk_id: str
    quote: str = Field(min_length=1, max_length=600)


class RagAnswerDraft(Contract):
    status: Literal["answered", "insufficient_evidence"]
    selections: list[QuoteSelection] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def valid_status(self):
        if (self.status == "answered") != bool(self.selections):
            raise ValueError("Answer status and quotes disagree")
        return self


class DocumentCitation(Contract):
    """A server-built reference to one immutable original, never a model URL."""

    model_config = ConfigDict(extra="forbid", strict=True)
    label: Literal["Source 1", "Source 2", "Source 3", "Source 4"]
    generation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    document_id: str = Field(pattern=r"^[a-z0-9-]{1,128}$")
    chunk_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    format: Literal["pdf", "md"]
    filename: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.(?:pdf|md)$")
    version: str = Field(min_length=1, max_length=64)
    page: int | None = Field(default=None, ge=1, le=12)
    section: str | None = Field(default=None, min_length=1, max_length=300)
    line_start: int | None = Field(default=None, ge=1, le=100000)
    line_end: int | None = Field(default=None, ge=1, le=100000)

    @model_validator(mode="after")
    def location_and_format(self):
        if not self.filename.endswith("." + self.format) or ".." in self.filename:
            raise ValueError("Invalid original filename")
        if any(not c.isprintable() for c in self.version + (self.section or "")):
            raise ValueError("Invalid citation display text")
        if self.format == "pdf":
            if self.page is None or any(v is not None for v in (self.section, self.line_start, self.line_end)):
                raise ValueError("PDF citations require only a page location")
        elif self.page is not None or not self.section or self.line_start is None or self.line_end is None or self.line_end < self.line_start:
            raise ValueError("Markdown citations require a section and ordered lines")
        return self


class RagTaskSummary(Contract):
    """Safe per-turn coverage metadata, without drafts or document text."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    task_id: str = Field(pattern=r"^task-[1-4]$")
    restaurant_id: str = Field(pattern=r"^demo-[a-z0-9-]+$", max_length=128)
    criterion: Literal["menu_item_price", "cancellation_policy"]
    status: Literal["supported", "missing", "unavailable", "invalid"]
    reason: Literal["verified", "unsupported_price_format", "missing_evidence", "unsupported_policy_layout",
                    "provider_error", "deadline_exhausted", "invalid_evidence", "invalid_selection", "conflicting_evidence"]
    source_label: Literal["Source 1", "Source 2", "Source 3", "Source 4"] | None = None

    @model_validator(mode="after")
    def coherent(self):
        reasons = {"supported": {"verified", "unsupported_price_format"},
                   "missing": {"missing_evidence", "unsupported_policy_layout"},
                   "unavailable": {"provider_error", "deadline_exhausted"},
                   "invalid": {"invalid_evidence", "invalid_selection", "conflicting_evidence"}}
        if self.reason not in reasons[self.status] or (self.source_label is not None) != (self.status == "supported"):
            raise ValueError("Task summary status/reason/source mismatch")
        if self.criterion == "cancellation_policy" and self.reason == "unsupported_price_format":
            raise ValueError("Policy task cannot carry a price reason")
        if self.criterion == "menu_item_price" and self.reason == "unsupported_policy_layout":
            raise ValueError("Menu task cannot carry a policy layout reason")
        return self


class RagCoverage(Contract):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    tasks: list[RagTaskSummary] = Field(min_length=2, max_length=4)
    required: int = Field(ge=2, le=4)
    supported: int = Field(ge=0, le=4)

    @model_validator(mode="after")
    def coherent(self):
        supported = [task for task in self.tasks if task.status == "supported"]
        if self.required != len(self.tasks) or self.supported != len(supported):
            raise ValueError("Coverage differs from task summaries")
        if [task.task_id for task in self.tasks] != [f"task-{i}" for i in range(1, self.required + 1)]:
            raise ValueError("Coverage task IDs must be complete and ordered")
        if len({(task.restaurant_id, task.criterion) for task in self.tasks}) != self.required:
            raise ValueError("Duplicate coverage task scope")
        if len({task.restaurant_id for task in self.tasks}) > 2:
            raise ValueError("Too many coverage restaurants")
        ids = list(dict.fromkeys(t.restaurant_id for t in self.tasks))
        if ({t.criterion for t in self.tasks} != {"menu_item_price", "cancellation_policy"}
                or {t.restaurant_id for t in self.tasks if t.criterion == "menu_item_price"} != set(ids)
                or self.tasks != sorted(self.tasks, key=lambda t: (ids.index(t.restaurant_id), t.criterion != "menu_item_price"))):
            raise ValueError("Coverage must have canonical mixed tasks")
        if [task.source_label for task in supported] != [f"Source {i}" for i in range(1, len(supported) + 1)]:
            raise ValueError("Coverage sources must be sequential")
        return self


class RagOutcome(Contract):
    status: Literal["answered", "partial", "clarify", "insufficient_evidence", "disabled", "unavailable", "invalid_answer"]
    text: str
    generation_id: str | None = None
    restaurant_id: str | None = None
    retrieval_count: int = 0
    citations: list[DocumentCitation] = Field(default_factory=list, max_length=4)
    mode: Literal["single", "comparison", "multipart"] | None = None
    coverage: RagCoverage | None = None
    context_candidate: DocumentContextDraft | None = None

    @model_validator(mode="after")
    def citation_status(self):
        if self.context_candidate is not None:
            candidate = self.context_candidate
            if (self.status not in {"answered", "partial"} or not self.citations
                    or candidate.generation_id != self.generation_id
                    or (self.mode is not None and candidate.origin_mode != self.mode)
                    or (candidate.origin_mode == "single" and candidate.restaurant_ids != (self.restaurant_id,))):
                raise ValueError("Context differs from validated answer")
        if self.citations and self.status not in {"answered", "partial"}:
            raise ValueError("Only answered/partial outcomes can have citations")
        cap = {None: 3, "single": 3, "comparison": 2, "multipart": 4}[self.mode]
        if len(self.citations) > cap:
            raise ValueError("Citation count exceeds mode limit")
        if self.mode != "multipart" and self.coverage is not None:
            raise ValueError("Coverage requires multipart mode")
        if self.mode != "multipart" and self.status == "partial" and (
                self.mode == "single" or len(self.citations) != 1 or self.restaurant_id is not None):
            raise ValueError("Partial comparison requires one source and no single scope")
        if any(c.generation_id != self.generation_id for c in self.citations):
            raise ValueError("Citation generation differs from the answer")
        if self.mode == "multipart":
            if self.restaurant_id is not None:
                raise ValueError("Multipart outcomes cannot advance single scope")
            if self.status in {"answered", "partial"}:
                if self.coverage is None or self.generation_id is None:
                    raise ValueError("Multipart answers require pinned coverage")
                count, total = self.coverage.supported, self.coverage.required
                expected_status = "answered" if count == total else "partial" if 0 < count < total else None
                if self.status != expected_status or any(task.status == "invalid" for task in self.coverage.tasks):
                    raise ValueError("Multipart status differs from coverage")
                labels = [task.source_label for task in self.coverage.tasks if task.status == "supported"]
                if [citation.label for citation in self.citations] != labels:
                    raise ValueError("Multipart citation coverage mismatch")
            elif self.coverage is not None and self.coverage.supported:
                raise ValueError("Failure outcome cannot publish supported coverage")
        return self


def validate_approved_document_payload(mode, status, generation_id, citations, coverage=None):
    """Recheck the parent approval boundary and final-turn extraction identically."""
    references = [DocumentCitation.model_validate(c) for c in citations]
    # Older callers do not carry a generation field in their turn fixtures.
    generation = generation_id if mode == "multipart" else generation_id or (
        references[0].generation_id if references else None)
    outcome = RagOutcome(mode=mode, status=status or "answered", text="approved",
                         generation_id=generation, citations=references, coverage=coverage)
    return outcome.citations, outcome.coverage


class QueryRewrite(Contract):
    query: str = Field(min_length=1, max_length=1000)
