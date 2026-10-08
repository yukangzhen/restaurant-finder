"""Validated contracts shared by ingestion and read-only document answering."""
from __future__ import annotations

import hashlib
import json
import math
import struct
import unicodedata
from importlib.metadata import version as package_version
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class DocumentSpec(Contract):
    document_id: str = Field(pattern=r"^[a-z0-9-]+$")
    restaurant_id: str
    path: str
    document_type: Literal["menu", "policy"]
    version: str = Field(min_length=1, max_length=64)


class CorpusSpec(Contract):
    fictional: Literal[True]
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
            raise ValueError("Corpus must contain 1 to 6 documents")
        return self


class ExtractedUnit(Contract):
    text: str
    page: int | None = Field(default=None, ge=1)
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


class ChunkReference(ChunkRecord):
    key: str


class SourceReference(DocumentSpec):
    source_hash: str
    key: str


class GenerationManifest(Contract):
    schema_version: Literal[1] = 1
    generation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    config: RagConfig
    restaurants: list[RestaurantEntry]
    sources: list[SourceReference]
    chunks: list[ChunkReference] = Field(min_length=1, max_length=48)

    @model_validator(mode="after")
    def integrity(self):
        restaurant_ids = {r.restaurant_id for r in self.restaurants}
        sources = {s.document_id: s for s in self.sources}
        if len(sources) != len(self.sources) or len({c.chunk_id for c in self.chunks}) != len(self.chunks):
            raise ValueError("Duplicate manifest IDs")
        root = f"rag/generations/{self.generation_id}/"
        for source in self.sources:
            if source.restaurant_id not in restaurant_ids or not source.key.startswith(root + "sources/") or ".." in source.key:
                raise ValueError("Invalid source reference")
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
        fingerprint = {"config": self.config.model_dump(), "restaurants": [r.model_dump() for r in self.restaurants],
                       "sources": sorted([[s.document_id, s.restaurant_id, s.document_type, s.version, s.source_hash] for s in self.sources])}
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
    distance: float
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
    label: Literal["Source 1", "Source 2", "Source 3"]
    generation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    document_id: str = Field(pattern=r"^[a-z0-9-]{1,128}$")
    chunk_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    format: Literal["pdf", "md"]
    filename: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.(?:pdf|md)$")
    version: str = Field(min_length=1, max_length=64)
    page: int | None = Field(default=None, ge=1, le=10)
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


class RagOutcome(Contract):
    status: Literal["answered", "clarify", "insufficient_evidence", "disabled", "unavailable", "invalid_answer"]
    text: str
    generation_id: str | None = None
    restaurant_id: str | None = None
    retrieval_count: int = 0
    citations: list[DocumentCitation] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def citation_status(self):
        if self.citations and self.status != "answered":
            raise ValueError("Only an answered outcome can have citations")
        if any(c.generation_id != self.generation_id for c in self.citations):
            raise ValueError("Citation generation differs from the answer")
        return self


class QueryRewrite(Contract):
    query: str = Field(min_length=1, max_length=1000)
