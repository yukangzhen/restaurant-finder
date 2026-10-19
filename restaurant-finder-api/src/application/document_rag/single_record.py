"""Complete admitted single-answer records using only selected verified passages."""
from __future__ import annotations

import re

from src.application.document_rag.comparison import menu_records
from src.application.document_rag.multipart import policy_record, validate_passages, validate_task_selection
from src.domain.document_multipart import MultipartTask
from src.domain.document_rag import QuoteSelection, RagAnswerDraft, canonical_text

CLARIFICATION = "Please name one menu item for its price, or ask about the restaurant's cancellation policy."


class RecordClarification(ValueError):
    """A price/policy task cannot be admitted without guessing its requested item."""


class PolicyRecordUnavailable(ValueError):
    """A missing/unsupported controlled policy is distinct from a forged quote."""

    def __init__(self, reason):
        if reason not in {"missing_evidence", "unsupported_policy_layout"}:
            raise ValueError("Unexpected policy availability reason")
        self.reason = reason
        super().__init__(reason)


def _intent_text(question, manifest):
    text = canonical_text(question).replace("\u2019", "'")
    spans = [match.span() for venue in manifest.restaurants for alias in [venue.name, *venue.aliases]
             for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I)]
    characters = list(text)
    for start, end in spans:
        characters[start:end] = [" "] * (end-start)
    return canonical_text("".join(characters))


def compile_single_tasks(question, restaurant_id, manifest):
    """Admit the existing price/cancellation forms without model-derived scope.

    An empty tuple means an unrelated/general question. A recognized but
    ambiguous price request raises clarification rather than using that escape.
    """
    venue = next((r for r in manifest.restaurants if r.restaurant_id == restaurant_id), None)
    if venue is None or len(question) > 1000:
        raise RecordClarification()
    text = _intent_text(question, manifest)
    policy = bool(re.search(r"\bcancel\w*\b", text, re.I))
    price = bool(re.search(r"\b(?:prices?|costs?)\b|\bhow much (?:is|does)\b", text, re.I))
    item = None
    if price:
        patterns = (r"\bwhat (?:is|are) (?:the )?(.+?) (?:prices?|costs?)\b(?!\s+of\b)",
                    r"\bhow much (?:is|does) (?:the )?(.+?)(?: cost)?[?.!]*\s*$",
                    r"\b(?:prices?|costs?) of (?:the )?(.+?)[?.!]*\s*$",
                    r"^(?!according\b|what\b|how\b|for\b)(?:the )?(.+?) prices?[?.!]*\s*$")
        matches = [m for pattern in patterns if (m := re.search(pattern, text, re.I))]
        if not matches:
            raise RecordClarification()
        items = {canonical_text(m[1]).rstrip(" .?!").casefold() for m in matches}
        if len(items) != 1:
            raise RecordClarification()
        item = items.pop()
        if (not 1 <= len(item) <= 80 or not all(c.isalnum() or c in " '-" for c in item)
                or re.search(r"\b(and|or|cancel\w*|polic\w*|menu|ingredients|allerg\w*)\b", item, re.I)):
            raise RecordClarification()
        if not any(menu_records(c.text, item, c.section) for c in manifest.chunks
                   if c.restaurant_id == restaurant_id and c.document_type == "menu"):
            raise RecordClarification()
    tasks = []
    for criterion in (["menu_item_price"] if price else []) + (["cancellation_policy"] if policy else []):
        tasks.append(MultipartTask(task_id=f"task-{len(tasks)+1}", restaurant_id=restaurant_id,
                     restaurant_name=venue.name, criterion=criterion,
                     item=item if criterion == "menu_item_price" else None))
    return tuple(tasks)


def _complete_menu(task, quote, selected, evidence):
    candidates = [(e, record) for e in evidence for record in menu_records(e.text, task.item, e.section)]
    if not candidates or any(not record[2] for _, record in candidates):
        raise ValueError("Menu record boundary is not known")
    if len({record[0] for _, record in candidates}) != 1:
        raise ValueError("Conflicting complete menu records")
    anchored = []
    for e, (body, sentence, _) in candidates:
        # Anchor includes the title AND complete price, with the optional final
        # period missing in the observed L1. A number or other dish cannot match.
        head = body[:body.index(sentence)+len(sentence)]
        if (e.chunk_id == selected.chunk_id and body.startswith(quote)
                and len(quote) >= len(head.rstrip("."))):
            anchored.append(body)
    if len(anchored) != 1 or len(anchored[0]) > 600:
        raise ValueError("Menu selection does not identify one complete record")
    return anchored[0]


def _complete_policy(task, quote, selected, evidence, manifest):
    record, reason = policy_record(task, evidence, manifest)
    if record is None:
        raise PolicyRecordUnavailable(reason)
    if record[0].chunk_id != selected.chunk_id:
        raise ValueError("Policy record is unavailable in the selected passage")
    _, body = record
    sentences = re.split(r"(?<=[.!?])\s+", body)
    if quote != body and not any(quote.rstrip(".") == sentence.rstrip(".")
            and re.search(r"\bcancel\w*\b", sentence, re.I) for sentence in sentences):
        raise ValueError("Policy selection must anchor a complete cancellation sentence")
    return body, record


def complete_single_selections(question, restaurant_id, draft, evidence, manifest):
    """Extend authentic anchors, then independently validate complete task coverage.

    No I/O or inference occurs here. The workflow alone publishes the final
    rendered answer, after the existing output approval boundary.
    """
    from src.application.document_rag.workflow import render_document_answer

    draft = RagAnswerDraft.model_validate(draft)
    if draft.status != "answered":
        return draft
    # Check the ORIGINAL quote and original-source provenance before any repair.
    render_document_answer(draft, evidence, manifest)
    tasks = compile_single_tasks(question, restaurant_id, manifest)
    if not tasks:
        return draft
    if len(evidence) > 5 or sum(len(e.text) for e in evidence) > 9000:
        raise ValueError("Single-answer evidence exceeds bounds")
    by_type = {kind: [e for e in evidence if e.document_type == kind] for kind in ("menu", "policy")}
    for kind, passages in by_type.items():
        # Validate even unselected passages; no foreign venue/type can be used
        # to manufacture a conflict or supply completion text.
        task = MultipartTask(task_id="task-1", restaurant_id=restaurant_id,
            restaurant_name=tasks[0].restaurant_name, criterion="menu_item_price" if kind=="menu" else "cancellation_policy",
            item="evidence" if kind=="menu" else None)
        validate_passages(task, passages, manifest)
    if len({e.chunk_id for e in evidence}) != len(evidence):
        raise ValueError("Duplicate retrieved passage")
    by_id = {e.chunk_id:e for e in evidence}
    completed, covered = [], {}
    for selection in draft.selections:
        selected = by_id[selection.chunk_id]
        task = next((t for t in tasks if t.document_type == selected.document_type), None)
        if task is None:
            raise ValueError("Selection is outside admitted tasks")
        quote = canonical_text(selection.quote)
        record = None
        if task.criterion == "menu_item_price":
            body = _complete_menu(task, quote, selected, by_type["menu"])
        else:
            body, record = _complete_policy(task, quote, selected, by_type["policy"], manifest)
        fixed = QuoteSelection(chunk_id=selection.chunk_id, quote=body)
        checked = RagAnswerDraft(status="answered", selections=[fixed])
        row = validate_task_selection(task, checked, by_type[task.document_type], manifest, record=record)
        if row.status != "supported":
            raise ValueError("Complete selection did not pass task validation")
        if task.criterion in covered:
            if covered[task.criterion] != fixed:
                raise ValueError("Multiple selected records for one task")
        else:
            completed.append(fixed)
            covered[task.criterion] = fixed
    if len(covered) != len(tasks):
        raise ValueError("Single answer omitted a requested task")
    return RagAnswerDraft(status="answered", selections=completed)
