"""Inspect immutable, hash-verified originals in the local Chainlit demo."""
from __future__ import annotations

import asyncio
import hashlib
import html
import logging
import re
from typing import Literal

import chainlit as cl
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_SOURCE_BYTES = 5 * 1024 * 1024
SOURCE_TIMEOUT_SECONDS = 30
SOURCE_UNAVAILABLE = "The source document is temporarily unavailable."
_s3_client = None
logger = logging.getLogger(__name__)


class Citation(BaseModel):
    """Validate the SSE boundary independently of the API's Python package."""

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
                raise ValueError("Invalid PDF location")
        elif self.page is not None or not self.section or self.line_start is None or self.line_end is None or self.line_end < self.line_start:
            raise ValueError("Invalid Markdown location")
        return self

    @property
    def source_key(self):
        return f"rag/generations/{self.generation_id}/sources/{self.document_id}.{self.format}"


def validate_citations(values, answer):
    if not isinstance(values, list) or not 1 <= len(values) <= 3:
        raise ValueError("Invalid citation list")
    citations = [Citation.model_validate(value) for value in values]
    for index, citation in enumerate(citations, 1):
        if citation.label != f"Source {index}" or answer.count(f"Source: {citation.label} — ") != 1:
            raise ValueError("Citation label does not match the complete answer")
    if len({c.generation_id for c in citations}) != 1:
        raise ValueError("Mixed source generations")
    return citations


def _get_s3_client(region):
    global _s3_client
    if _s3_client is None:
        import boto3
        from botocore.config import Config
        _s3_client = boto3.client("s3", region_name=region, config=Config(
            connect_timeout=3, read_timeout=10, retries={"total_max_attempts": 1},
        ))
    return _s3_client


def load_original(citation, bucket, region):
    """Read only the derived source key, bounded and closed even on failure."""
    response = _get_s3_client(region).get_object(Bucket=bucket, Key=citation.source_key)
    body = response["Body"]
    try:
        length = response.get("ContentLength")
        if type(length) is not int or not 0 < length <= MAX_SOURCE_BYTES:
            raise ValueError("Invalid source size")
        content = body.read(MAX_SOURCE_BYTES + 1)
        if not content or len(content) != length or len(content) > MAX_SOURCE_BYTES:
            raise ValueError("Incomplete or oversized source")
    finally:
        body.close()
    if hashlib.sha256(content).hexdigest() != citation.source_hash:
        raise ValueError("Original source hash mismatch")
    if citation.format == "pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF signature")
    else:
        content.decode("utf-8", errors="strict")
    return content


def _display_text(value):
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", html.escape(value, quote=True))


def markdown_view(citation, content):
    """Full original text in a literal block, with separate location annotations."""
    text = content.decode("utf-8", errors="strict")
    lines = text.splitlines()
    if citation.line_end > len(lines):
        raise ValueError("Citation lies outside the original")
    fence = "`" * max(3, 1 + max((len(run) for run in re.findall(r"`+", text)), default=0))
    numbered = "\n".join(f"{index:>4} | {line}" for index, line in enumerate(lines, 1))
    return (
        f"Document: {citation.document_id}; version {_display_text(citation.version)}\n\n"
        f"Cited section: {_display_text(citation.section)}; lines {citation.line_start}–{citation.line_end}\n\n"
        f"Generation: {citation.generation_id[:12]}. Line numbers are viewer annotations.\n\n"
        f"{fence}text\n{numbered}\n{fence}"
    )


def viewer_name(citation, answer_number):
    if type(answer_number) is not int or not 1 <= answer_number <= 1000000:
        raise ValueError("Invalid answer reference number")
    return f"{citation.label} (answer {answer_number})"


def make_elements(citation, content, answer_number=1):
    name = viewer_name(citation, answer_number)
    if citation.format == "pdf":
        viewer = cl.Pdf(name=name, content=content, display="side", page=citation.page)
    else:
        viewer = cl.Text(name=name, content=markdown_view(citation, content), display="side")
    original = cl.File(name=f"{name} original — {citation.filename}", content=content,
                       display="inline", mime="application/pdf" if citation.format == "pdf" else "application/octet-stream")
    return [viewer, original]


async def prepare_source_elements(values, answer, bucket, region, answer_number=1):
    """No agent retries; a source failure leaves the approved answer available."""
    elements = []
    links = {}
    unavailable = False
    try:
        citations = validate_citations(values, answer)
        if not bucket:
            raise ValueError("Source bucket is unconfigured")
        originals = {}
        # Consistency is checked before any network access, including duplicates.
        for citation in citations:
            identity = (citation.source_hash, citation.format, citation.filename, citation.version)
            if citation.source_key in originals and originals[citation.source_key] != identity:
                raise ValueError("Conflicting original references")
            originals[citation.source_key] = identity
        originals = {}
        async with asyncio.timeout(SOURCE_TIMEOUT_SECONDS):
            for citation in citations:
                try:
                    if citation.source_key not in originals:
                        # Cache failed reads too, so a duplicate never causes a retry.
                        originals[citation.source_key] = None
                        originals[citation.source_key] = await asyncio.to_thread(load_original, citation, bucket, region)
                    content = originals[citation.source_key]
                    if content is None:
                        raise ValueError("Original unavailable")
                    elements.extend(make_elements(citation, content, answer_number))
                    links[citation.label] = viewer_name(citation, answer_number)
                except Exception as error:
                    unavailable = True
                    logger.warning("Source inspection unavailable (error_type=%s)", type(error).__name__)
    except Exception as error:
        unavailable = True
        logger.warning("Source preparation unavailable (error_type=%s)", type(error).__name__)
    return elements, SOURCE_UNAVAILABLE if unavailable else "", links
