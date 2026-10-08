"""Offline source validation, extraction, and record-preserving chunking."""
from __future__ import annotations

import json
import re
from pathlib import Path, PureWindowsPath

from src.domain.document_rag import ChunkRecord, CorpusSpec, DocumentSpec, ExtractedUnit, canonical_text, digest


def load_corpus(path: Path) -> tuple[CorpusSpec, dict[str, bytes]]:
    corpus = CorpusSpec.model_validate_json(path.read_text(encoding="utf-8"))
    root = path.resolve().parent
    sources = {}
    for doc in corpus.documents:
        relative = Path(doc.path)
        # Catalog paths must stay relative on both Windows and Linux runners.
        windows_path = PureWindowsPath(doc.path)
        candidate = (root / relative).resolve()
        if (
            windows_path.drive or windows_path.root or relative.is_absolute()
            or not candidate.is_relative_to(root)
            or candidate.suffix.lower() not in {".md", ".pdf"}
        ):
            raise ValueError("Source must be a Markdown/PDF file inside the corpus directory")
        if candidate.stat().st_size > 5 * 1024 * 1024:
            raise ValueError("Document exceeds 5 MiB")
        sources[doc.document_id] = candidate.read_bytes()
    return corpus, sources


def extract_units(data: bytes, suffix: str) -> list[ExtractedUnit]:
    if suffix.lower() == ".pdf":
        from io import BytesIO
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 10:
            raise ValueError("PDF must be unencrypted with 1 to 10 pages")
        units = []
        for index, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if not text.strip():
                raise ValueError("PDF page has no extractable text; OCR is unsupported")
            units.append(ExtractedUnit(text=text, page=index))
    elif suffix.lower() == ".md":
        lines = data.decode("utf-8-sig").splitlines()
        units, section, start, buffer = [], "Document", 1, []
        for number, line in enumerate(lines, 1):
            match = re.match(r"^#{1,6}\s+(.+)", line)
            if match:
                if any(x.strip() for x in buffer):
                    units.append(ExtractedUnit(text="\n".join(buffer), section=section, line_start=start, line_end=number-1))
                section, start, buffer = match.group(1), number, [line]
            else:
                buffer.append(line)
        if any(x.strip() for x in buffer):
            units.append(ExtractedUnit(text="\n".join(buffer), section=section, line_start=start, line_end=len(lines)))
    else:
        raise ValueError("Unsupported source format")
    if not units or sum(len(u.text) for u in units) > 100000:
        raise ValueError("Document is empty or exceeds 100,000 extracted characters")
    return units


def chunk_document(spec: DocumentSpec, data: bytes) -> list[ChunkRecord]:
    """Keep complete paragraphs/menu rows within a single page or section."""
    output = []
    source_hash = digest(data)
    for unit in extract_units(data, Path(spec.path).suffix):
        # Blank lines delimit paragraphs; each PDF line is a complete demo menu record.
        blocks = re.split(r"\n\s*\n", unit.text) if unit.page is None else unit.text.splitlines()
        records = [canonical_text(x) for x in blocks if canonical_text(x)]
        if any(len(x) > 1800 for x in records):
            raise ValueError("Indivisible record exceeds the chunk limit")
        groups, current = [], []
        for record in records:
            if len(" ".join([*current, record])) > 1800:
                groups.append(" ".join(current))
                overlap = current[-1] if current and len(current[-1]) <= 200 else None
                current = [overlap, record] if overlap and len(overlap) + len(record) + 1 <= 1800 else [record]
            else:
                current.append(record)
        if current:
            groups.append(" ".join(current))
        location = unit.model_dump(exclude={"text"})
        for text in groups:
            output.append(ChunkRecord(**location, text=text, chunk_id=digest([spec.document_id, source_hash, location, text]),
                                      document_id=spec.document_id, source_hash=source_hash, text_hash=digest(text),
                                      restaurant_id=spec.restaurant_id, document_type=spec.document_type, version=spec.version))
    return output
