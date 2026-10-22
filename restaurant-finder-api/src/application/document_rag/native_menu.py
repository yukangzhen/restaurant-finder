"""Reviewed native PDF row boundaries; all answer text stays in retrieved evidence."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re

from src.domain.document_rag import EvidenceIntegrityError, QuoteSelection, RagAnswerDraft, canonical_text


@dataclass(frozen=True)
class NativeRecord:
    quote: str
    amount: Decimal
    currency: str | None
    charge_note: str | None
    evidence: object
    category: str
    anchor_length: int


def is_native_venue(restaurant_id, manifest):
    return any(s.restaurant_id == restaurant_id and s.native_menu for s in manifest.sources)


def native_lookup_query(query, manifest):
    """Expand lookup tokens with reviewed native spelling, never answer text."""
    if query.document_type != "menu":
        return query.query
    spellings = [anchor.start for source in manifest.sources
        if source.restaurant_id == query.restaurant_id and source.native_menu
        for anchor in source.native_menu.records
        if re.search(r"(?<!\w)"+re.escape(canonical_text(anchor.item))+r"(?!\w)", query.query, re.I)]
    return " ".join([query.query, *dict.fromkeys(spellings)])


def registered_records(item, restaurant_id, evidence, manifest):
    """Compile reviewed boundaries only after checking the exact pinned passage."""
    refs = {c.chunk_id: c for c in manifest.chunks}
    sources = {s.document_id: s for s in manifest.sources}
    results = []
    for passage in evidence:
        source = sources.get(passage.document_id)
        if not source or not source.native_menu or source.restaurant_id != restaurant_id:
            continue
        ref = refs.get(passage.chunk_id)
        if (ref is None or passage.generation_id != manifest.generation_id
                or any(getattr(passage, field) != getattr(ref, field) for field in
                       ("document_id", "restaurant_id", "document_type", "version", "source_hash", "text_hash", "text", "page"))
                or ref.source_hash != source.source_hash):
            raise EvidenceIntegrityError("Native row differs from pinned original")
        for anchor in source.native_menu.records:
            if canonical_text(anchor.item).casefold() != canonical_text(item).casefold() or passage.page != anchor.page:
                continue
            start, end = canonical_text(anchor.start), canonical_text(anchor.end)
            matches = list(re.finditer(r"(?<![\w'-])"+re.escape(start)+r"\s+(.+?)(?=\s+"+re.escape(end)+r"(?:\s|$))", passage.text, re.I))
            # A split row is not silently reconstructed from another passage.
            if not matches:
                continue
            if len(matches) != 1:
                raise EvidenceIntegrityError("Ambiguous native menu boundary")
            match = matches[0]
            if not re.search(r"(?<!\w)"+re.escape(anchor.category)+r"(?!\w)", passage.text[:match.start()], re.I):
                raise EvidenceIntegrityError("Native menu category is missing")
            captured_page = source.provenance.kind == "menu_page_pdf"
            note = canonical_text(anchor.charge_note) if anchor.charge_note is not None else None
            if note is None and not captured_page:
                raise EvidenceIntegrityError("Only a captured menu page may omit a printed charge note")
            if note is not None and passage.text.count(note) != 1:
                raise EvidenceIntegrityError("Native menu charge note is missing or ambiguous")
            body = canonical_text(match[1])
            price_token = r"(?P<price>\d{1,8}(?:\.\d{1,2})?)"
            if captured_page:
                # Preserve the page's actual currency token; do not rewrite the
                # original into the numeric-only grammar of issued menu PDFs.
                price_token = r"(?P<currency>RM|MYR)\s*" + price_token
            pattern = (price_token + r"\s+(?P<description>.+)" if anchor.price_position == "after_title"
                       else r"(?P<description>.+?)\s+" + price_token)
            parsed = re.fullmatch(pattern, body)
            if not parsed or not re.search(r"[A-Za-z]", parsed["description"]):
                raise EvidenceIntegrityError("Native item amount is not adjacent to its record")
            if captured_page and source.native_menu.currency != "MYR":
                raise EvidenceIntegrityError("Menu-page currency differs from reviewed MYR evidence")
            quote = canonical_text(match[0])
            if len(quote) > 600:
                raise EvidenceIntegrityError("Native row exceeds the quote bound")
            anchor_length = (len(start)+1+parsed.end("price") if anchor.price_position == "after_title" else len(quote))
            results.append(NativeRecord(quote, Decimal(parsed["price"]), source.native_menu.currency, note,
                                        passage, anchor.category, anchor_length))
    # Duplicated retrieval of the exact same row is harmless; different categories,
    # pages or source records require clarification, even if their amounts match.
    unique = {(r.evidence.document_id, r.evidence.page, r.category, r.quote): r for r in results}
    if len(unique) > 1:
        raise EvidenceIntegrityError("More than one native item record matches")
    return list(unique.values())


def native_draft(item, restaurant_id, evidence, manifest):
    if not is_native_venue(restaurant_id, manifest):
        return None
    rows = registered_records(item, restaurant_id, evidence, manifest)
    return (RagAnswerDraft(status="answered", selections=[QuoteSelection(chunk_id=rows[0].evidence.chunk_id, quote=rows[0].quote)])
            if rows else RagAnswerDraft(status="insufficient_evidence"))


def price_fact(record):
    from src.domain.document_comparison import PriceFact
    return PriceFact(amount=record.amount, currency=record.currency, unit="listed_item") if record.currency else None


def unit_suffix(unit):
    return " (listed item; portion size not compared)" if unit == "listed_item" else f" per {unit}"
