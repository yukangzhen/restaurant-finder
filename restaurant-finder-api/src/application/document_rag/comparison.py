"""Deterministic admission, relevant-record validation and comparison arithmetic."""
from __future__ import annotations

import re
from decimal import Decimal

from src.domain.document_comparison import ComparisonPlan, ComparisonResult, ComparisonRow, PriceFact
from src.domain.document_rag import QuoteSelection, RagAnswerDraft, canonical_text

CLARIFICATION = ("Please name two different fictional catalog restaurants and one menu item to compare. "
                 "For example: Compare mushroom pasta prices at Harbor and Sakura. Show the sources.")
INVALID = "I couldn't validate the document comparison. Please rephrase your question."
UNAVAILABLE = "The document comparison is temporarily unavailable. Please try again later."
INSUFFICIENT = "The retrieved menus do not contain enough evidence to compare that item."


def is_comparison_candidate(question: str) -> bool:
    text = canonical_text(question).casefold()
    return bool(re.search(r"\b(compare|comparison|difference|cheaper)\b", text)
                and re.search(r"\b(prices?|costs?|cheaper)\b", text))


def plan_comparison(question, manifest):
    """Return an explicit plan, or None for a candidate needing clarification."""
    text = canonical_text(question)
    if len(text) > 1000 or any(not char.isprintable() and not char.isspace() for char in question):
        return None
    text = re.sub(r"[.!?]?\s*show (?:the )?sources[.!?]?\s*$", "", text, flags=re.I).rstrip(" .!?")
    forms = [r"compare (?:the )?(.+?) prices? at (.+?) and (.+)",
             r"what is the price difference for (?:the )?(.+?) between (.+?) and (.+)",
             r"which is cheaper for (?:the )?(.+?):\s*(.+?) or (.+)"]
    match = next((m for pattern in forms if (m := re.fullmatch(pattern, text, flags=re.I))), None)
    if match is None:
        return None
    item, left, right = match.groups()
    if not 1 <= len(item) <= 80 or not all(c.isalnum() or c in " '-" for c in item):
        return None
    if re.search(r"\b(and|or|cancellation|parking|polic(?:y|ies)|allergies|ingredients)\b", item, re.I):
        return None
    aliases = [(canonical_text(alias).casefold(), restaurant.restaurant_id)
               for restaurant in manifest.restaurants for alias in [restaurant.name, *restaurant.aliases]]
    aliases.sort(key=lambda pair: len(pair[0]), reverse=True)
    def resolve(operand):
        ids = {value for alias, value in aliases if canonical_text(operand).casefold() == alias}
        return next(iter(ids)) if len(ids) == 1 else None
    pair = (resolve(left), resolve(right))
    if None in pair or pair[0] == pair[1]:
        return None
    return ComparisonPlan(restaurant_ids=pair, item=item, generation_id=manifest.generation_id)


def _records(text, item):
    """Controlled corpus grammar: a title-price sentence and adjacent qualifiers.

    Canonical extraction removes newlines. Recognized qualifiers end in periods;
    following dish entries/footer text are never swallowed into this record.
    Unrecognized attached prose disables arithmetic instead of guessing a boundary.
    """
    title = re.escape(canonical_text(item))
    pattern = rf"(?<![\w'-]){title}\s+-\s+([^!?]*?\.(?=\s|$))"
    for match in re.finditer(pattern, text, flags=re.I):
        # A shorter item must not match a suffix of a longer menu title.
        before = text[:match.start()].rstrip()
        if before and before[-1].isalnum() and not before.endswith("Main dishes"):
            continue
        end = match.end()
        remainder = text[end:]
        while qualifier := re.match(r"\s+(?:Contains|Available|Served|Vegan\b|Vegetarian\b)[^.]*\.", remainder, re.I):
            end += qualifier.end()
            remainder = text[end:]
        boundary_known = (not remainder.strip() or bool(re.match(
            r"\s+(?:[\w][\w '\-]{0,80}\s+-\s+|Controlled corpus fixture\b|#{1,3}\s)", remainder)))
        yield text[match.start():end], match.group(1), boundary_known


def menu_records(text, item, section=None):
    """Share controlled records without guessing beyond a known section heading.

    All callers use the same title/qualifier grammar. Verified section metadata
    may remove exactly that heading before the existing parser runs.
    Returned bodies remain contiguous substrings of the original passage.
    """
    if section:
        text = re.sub(r"^#{1,6}\s+" + re.escape(canonical_text(section)) + r"(?:\s+|$)", "", text)
    return tuple(_records(text, item))


def parse_price(price_sentence):
    match = re.fullmatch(r"(?:RM|MYR)\s*([0-9]{1,8}(?:\.[0-9]{1,2})?) per (serving|bowl|piece)\.",
                         price_sentence, re.I)
    if not match:
        return None
    return PriceFact(amount=Decimal(match[1]), unit=match[2].lower())


def validate_selection(plan, restaurant_id, draft, evidence, manifest):
    return validate_menu_selection(plan.item, plan.generation_id, restaurant_id, draft, evidence, manifest)


def validate_menu_selection(requested_item, generation_id, restaurant_id, draft, evidence, manifest):
    """Revalidate provenance and relevant complete item records before deriving values."""
    from src.application.document_rag.workflow import render_document_answer
    draft = RagAnswerDraft.model_validate(draft)
    prices = set()
    for passage in evidence:
        for _, sentence, _ in menu_records(passage.text, requested_item, passage.section):
            fact = parse_price(sentence)
            prices.add((fact.amount, fact.currency, fact.unit) if fact else canonical_text(sentence).casefold())
    if len(prices) > 1:
        return ComparisonRow(restaurant_id=restaurant_id, status="invalid", reason="conflicting_evidence", retrieval_started=True)
    if draft.status == "insufficient_evidence":
        return ComparisonRow(restaurant_id=restaurant_id, status="missing", reason="missing_evidence", retrieval_started=True)
    if len(draft.selections) != 1:
        raise ValueError("Exactly one branch quote required")
    selection = draft.selections[0]
    item = next((value for value in evidence if value.chunk_id == selection.chunk_id), None)
    if item is None or item.restaurant_id != restaurant_id or item.document_type != "menu":
        raise ValueError("Selection is outside branch scope")
    # This establishes exact quote and pinned original provenance, including location.
    render_document_answer(draft, evidence, manifest)
    if item.generation_id != generation_id:
        raise ValueError("Selection generation mismatch")
    quote = canonical_text(selection.quote)
    candidates = menu_records(item.text, requested_item, item.section)
    record = next((value for value in candidates if value[0] == quote), None)
    if record is None:
        raise ValueError("Selected quote is not the complete requested item record")
    fact = parse_price(record[1]) if record[2] else None
    return ComparisonRow(restaurant_id=restaurant_id, status="supported",
                         reason="verified" if fact else "unsupported_price_format", retrieval_started=True,
                         selection=QuoteSelection(chunk_id=selection.chunk_id, quote=quote), evidence=item, price=fact)


def aggregate_comparison(plan, rows, manifest):
    from src.application.document_rag.workflow import render_document_answer, safe_markdown
    if len(rows) != 2 or {row.restaurant_id for row in rows} != set(plan.restaurant_ids):
        raise ValueError("Exactly two planned results required")
    ordered = tuple(next(row for row in rows if row.restaurant_id == rid) for rid in plan.restaurant_ids)
    supported = [row for row in ordered if row.status == "supported"]
    invalid = any(row.status == "invalid" for row in ordered)
    status = ("invalid_answer" if invalid else "answered" if len(supported) == 2 else "partial" if supported
              else "unavailable" if any(row.status == "unavailable" for row in ordered) else "insufficient_evidence")
    reason = "invalid_evidence" if invalid else "incomplete_evidence"
    difference, cheaper_id, citations = None, None, []
    text = {"invalid_answer": INVALID, "unavailable": UNAVAILABLE, "insufficient_evidence": INSUFFICIENT}.get(status, "")
    if status in {"answered", "partial"}:
        names = {r.restaurant_id: r.name for r in manifest.restaurants}
        lines = ["Listed prices in the fictional demo documents:", "",
                 f"| Restaurant | Listed {safe_markdown(plan.item)} price | Evidence |", "| --- | --- | --- |"]
        source_index = 0
        for row in ordered:
            if row.status == "supported":
                source_index += 1
                value = f"RM{row.price.amount} per {row.price.unit}" if row.price else "Unsupported price format"
                label = f"Source {source_index}"
            else:
                value = "Not found in retrieved menu evidence" if row.status == "missing" else "Retrieval unavailable"
                label = "No verified source"
            lines.append(f"| {safe_markdown(names[row.restaurant_id])} | {value} | {label} |")
        lines.extend(["", f"Document evidence: {len(supported)} of 2 restaurants supported."])
        if len(supported) == 2:
            if any(row.price is None for row in supported):
                reason = "unsupported_price_format"
                lines.append("A price difference cannot be calculated because a listed price format is unsupported.")
            elif supported[0].price.unit != supported[1].price.unit:
                reason = "different_units"
                lines.append("A price difference cannot be calculated because the listed serving units differ.")
            else:
                a, b = (row.price.amount for row in supported)
                difference = abs(a-b)
                reason = "tie" if a == b else "calculated"
                cheaper_id = None if a == b else supported[0 if a < b else 1].restaurant_id
                lines.append(f"The listed prices are equal per {supported[0].price.unit}." if a == b else
                             f"{safe_markdown(names[cheaper_id])}'s listed price is RM{difference} lower per {supported[0].price.unit}.")
        else:
            lines.append("A price difference cannot be calculated because one restaurant has no verified result.")
        draft = RagAnswerDraft(status="answered", selections=[row.selection for row in supported])
        quotes, citations = render_document_answer(draft, [row.evidence for row in supported], manifest)
        text = "\n".join(lines) + "\n\n" + quotes
    return ComparisonResult(plan=plan, rows=ordered, status=status, coverage=len(supported), difference=difference,
                            cheaper_id=cheaper_id, calculation_reason=reason, text=text, citations=citations)
