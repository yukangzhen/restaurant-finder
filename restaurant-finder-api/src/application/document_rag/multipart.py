"""Pure admission, evidence checks and rendering for mixed document tasks."""
from __future__ import annotations

import re

from src.application.document_rag.comparison import validate_menu_selection
from src.domain.document_multipart import MultipartPlan, MultipartPlanDraft, MultipartRequest, MultipartResult, MultipartTask, MultipartTaskResult
from src.domain.document_rag import (
    DocumentCitation, EvidenceIntegrityError, QuoteSelection, RagAnswerDraft, RagCoverage, RagTaskSummary,
    RestaurantEntry, canonical_text, document_description,
)

CLARIFICATION = ("Please ask about one menu item's price and cancellation policies for one or two named fictional restaurants. "
                 "For example: Compare mushroom pasta prices at Harbor and Sakura, and explain both restaurants' cancellation policies.")
INVALID = "I couldn't validate the multi-part document answer. Please rephrase your question."
UNAVAILABLE = "Multi-part document answering is temporarily unavailable. Please try again later."
DISABLED = "Multi-part document answering is currently disabled."
INSUFFICIENT = "The active documents do not contain enough evidence for the requested parts."
REASONS = {"missing_evidence": "Not found in retrieved document evidence",
           "unsupported_policy_layout": "The policy layout cannot be validated by this workflow",
           "provider_error": "Retrieval or selection unavailable", "deadline_exhausted": "The shared deadline was exhausted"}


class PolicyConflict(EvidenceIntegrityError):
    """Distinct complete policies cannot be merged into one answer."""


def is_multipart_candidate(question):
    text = canonical_text(question).casefold()
    # Preserve the existing "According to ... menu and policy" single-question
    # path and the historical comparison clarification grammar.
    if not re.match(r"^(?:compare|for|what is)\b", text):
        return False
    if re.search(r"\bprices? and cancellation polic(?:y|ies) at\b", text):
        return False
    return bool(re.search(r"\b(?:prices?|costs?)\b.*\band\b.*\bcancel\w*\b", text))


def compile_multipart_request(question, catalog):
    text = canonical_text(question).replace("\u2019", "'")
    if len(text) > 1000 or any(not c.isprintable() and not c.isspace() for c in question):
        return None
    text = re.sub(r"[.!?]?\s+show the sources[.!?]?\s*$", "", text, flags=re.I).rstrip(" .!?")
    entries = [RestaurantEntry.model_validate(r) for r in getattr(catalog, "restaurants", catalog)]
    aliases = sorted([(canonical_text(alias).casefold(), r) for r in entries for alias in [r.name, *r.aliases]],
                     key=lambda pair: len(pair[0]), reverse=True)

    def resolve(operand):
        matches = {r.restaurant_id: r for alias, r in aliases if canonical_text(operand).casefold() == alias}
        return next(iter(matches.values())) if len(matches) == 1 else None

    forms = [
        (r"compare (?:the )?(.+?) prices? at (.+?) and (.+?), and explain both restaurants'? cancellation policies", "four"),
        (r"for (.+?) and (.+?), compare (?:the )?(.+?) prices? and their cancellation policies", "four_reordered"),
        (r"for (.+?), what is the (.+?) prices? and cancellation policy", "one"),
        (r"what is the (.+?) prices? at (.+?), and what is its cancellation policy", "one_reordered"),
        (r"compare (?:the )?(.+?) prices? at (.+?) and (.+?), and explain (.+?)'s cancellation policy", "three"),
    ]
    found = next(((m, kind) for pattern, kind in forms if (m := re.fullmatch(pattern, text, re.I))), None)
    if found is None:
        return None
    match, kind = found
    values = match.groups()
    if kind == "four_reordered":
        left, right, item = values
    elif kind == "one":
        left, item = values
        right = None
    elif kind == "one_reordered":
        item, left = values
        right = None
    else:
        item, left, right = values[:3]
    item = re.sub(r"^the\s+", "", canonical_text(item), flags=re.I).casefold()
    if not 1 <= len(item) <= 80 or not all(c.isalnum() or c in " '-" for c in item):
        return None
    if re.search(r"\b(and|or|cancellation|parking|polic(?:y|ies)|allerg\w*|ingredients|under|with|without|vegan|vegetarian|gluten)\b", item, re.I):
        return None
    if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", item, re.I) for alias, _ in aliases):
        return None
    a, b = resolve(left), resolve(right) if right else None
    if a is None or (right and (b is None or b.restaurant_id == a.restaurant_id)):
        return None
    restaurants = [a, b] if b else [a]
    policy_ids = {r.restaurant_id for r in restaurants}
    if kind == "three":
        c = resolve(values[3])
        if c is None or c.restaurant_id not in policy_ids:
            return None
        policy_ids = {c.restaurant_id}
    tasks = []
    for restaurant in restaurants:
        for criterion in ("menu_item_price", "cancellation_policy"):
            if criterion == "cancellation_policy" and restaurant.restaurant_id not in policy_ids:
                continue
            tasks.append(MultipartTask(task_id=f"task-{len(tasks)+1}", restaurant_id=restaurant.restaurant_id,
                restaurant_name=restaurant.name, criterion=criterion, item=item if criterion == "menu_item_price" else None))
    return MultipartRequest(question=canonical_text(question), tasks=tuple(tasks))


def validate_multipart_plan(request, draft, manifest):
    pinned = compile_multipart_request(request.question, manifest)
    if pinned is None or pinned.tasks != request.tasks:
        raise EvidenceIntegrityError("Pinned catalog differs from admitted scope")
    draft = MultipartPlanDraft.model_validate(draft)
    identities = [(t.restaurant_id, t.criterion, canonical_text(t.item).casefold() if t.item else None) for t in draft.tasks]
    if len(set(identities)) != len(identities) or set(identities) != {t.identity for t in request.tasks}:
        raise ValueError("Planner did not cover exact request")
    return MultipartPlan(**request.model_dump(), generation_id=manifest.generation_id)


def validate_passages(task, evidence, manifest):
    refs = {c.chunk_id: c for c in manifest.chunks}
    if len(evidence) > 5 or sum(len(e.text) for e in evidence) > 9000 or len({e.chunk_id for e in evidence}) != len(evidence):
        raise EvidenceIntegrityError("Evidence exceeds task bounds")
    for e in evidence:
        ref = refs.get(e.chunk_id)
        if (ref is None or e.generation_id != manifest.generation_id or e.restaurant_id != task.restaurant_id
                or e.document_type != task.document_type or any(getattr(e, f) != getattr(ref, f) for f in
                    ("document_id", "restaurant_id", "document_type", "version", "source_hash", "text_hash", "text",
                     "page", "section", "line_start", "line_end"))):
            raise EvidenceIntegrityError("Evidence differs from pinned task scope")


def policy_record(task, evidence, manifest):
    """Return a complete controlled section from Markdown or a captured policy PDF."""
    headings = {"reservations and cancellation", "cancelation policy", "cancellation policy"}
    docs = {s.document_id: s for s in manifest.sources}
    refs = [c for c in manifest.chunks if c.restaurant_id == task.restaurant_id and c.document_type == "policy"
            and (canonical_text(c.section or "").casefold() in headings or
                 (docs[c.document_id].provenance and docs[c.document_id].provenance.kind == "booking_page_pdf"))]
    if not refs:
        return None, "missing_evidence"
    bodies = []
    for ref in refs:
        source = docs[ref.document_id]
        if source.provenance and source.provenance.kind == "booking_page_pdf":
            # PDF lines become canonical page chunks. Both adjacent section
            # boundaries must survive in one retrieved chunk; never return a
            # partial policy, assemble fragments, or infer an omitted condition.
            starts = list(re.finditer(r"\b(?:Cancelation|Cancellation) Policy (?=Cancel with\b)", ref.text))
            if not starts:
                continue
            end = "How to Cancel or Amend"
            if (len(starts) != 1 or ref.text.count(end) != 1 or ref.page is None
                    or ref.section is not None):
                return None, "unsupported_policy_layout"
            start = starts[0].end()
            stop = ref.text.index(end)
            if stop <= start:
                return None, "unsupported_policy_layout"
            body = ref.text[start:stop].strip()
            if not body:
                return None, "unsupported_policy_layout"
            bodies.append((ref, body))
            continue
        if (sum(c.document_id == ref.document_id for c in refs) != 1
                or not docs[ref.document_id].path.lower().endswith(".md")):
            return None, "unsupported_policy_layout"
        body = re.sub(r"^#{1,6}\s+" + re.escape(ref.section) + r"(?:\s+|$)", "", ref.text, flags=re.I)
        if body == ref.text or not body:
            return None, "unsupported_policy_layout"
        bodies.append((ref, body))
    if not bodies:
        return None, "missing_evidence"
    if len({ref.document_id for ref, _ in bodies}) != len(bodies):
        return None, "unsupported_policy_layout"
    if len({body for _, body in bodies}) > 1:
        raise PolicyConflict("Conflicting complete cancellation policies")
    if any(len(body) > 600 for _, body in bodies):
        return None, "unsupported_policy_layout"
    by_id = {e.chunk_id: e for e in evidence}
    selected = next(((by_id[ref.chunk_id], body) for ref, body in sorted(bodies, key=lambda pair: (pair[0].document_id, pair[0].chunk_id))
                     if ref.chunk_id in by_id), None)
    return selected, "verified" if selected else "missing_evidence"


def validate_task_selection(task, draft, evidence, manifest, record=None):
    from src.application.document_rag.workflow import render_document_answer
    validate_passages(task, evidence, manifest)
    if task.criterion == "menu_item_price":
        row = validate_menu_selection(task.item, manifest.generation_id, task.restaurant_id, draft, evidence, manifest)
        return MultipartTaskResult(task=task, **row.model_dump(exclude={"restaurant_id"}))
    draft = RagAnswerDraft.model_validate(draft)
    if draft.status == "insufficient_evidence":
        return MultipartTaskResult(task=task, status="missing", reason="missing_evidence", retrieval_started=True)
    record = record or policy_record(task, evidence, manifest)[0]
    if record is None or len(draft.selections) != 1:
        raise ValueError("Exactly one complete policy record required")
    e, body = record
    selection = draft.selections[0]
    if selection.chunk_id != e.chunk_id or canonical_text(selection.quote) != body:
        raise ValueError("Policy selection omitted conditions or changed record")
    render_document_answer(draft, evidence, manifest)
    return MultipartTaskResult(task=task, status="supported", reason="verified", retrieval_started=True,
                               selection=QuoteSelection(chunk_id=e.chunk_id, quote=body), evidence=e)


def result_coverage(result):
    labels = {r.task.task_id: c.label for r, c in zip((r for r in result.rows if r.status == "supported"), result.citations)}
    return RagCoverage(required=len(result.rows), supported=result.supported, tasks=[RagTaskSummary(
        task_id=r.task.task_id, restaurant_id=r.task.restaurant_id, criterion=r.task.criterion, status=r.status,
        reason=r.reason, source_label=labels.get(r.task.task_id)) for r in result.rows])


def aggregate_multipart(plan, rows, manifest):
    from src.application.document_rag.workflow import render_document_answer, safe_markdown
    if len(rows) != len(plan.tasks) or {r.task.task_id for r in rows} != {t.task_id for t in plan.tasks}:
        raise ValueError("Missing or duplicate worker result")
    ordered = tuple(next(r for r in rows if r.task.task_id == task.task_id) for task in plan.tasks)
    if tuple(r.task for r in ordered) != plan.tasks:
        raise ValueError("Worker changed task identity")
    supported = [r for r in ordered if r.status == "supported"]
    invalid = any(r.status == "invalid" for r in ordered)
    status = ("invalid_answer" if invalid else "answered" if len(supported) == len(ordered) else "partial" if supported
              else "unavailable" if any(r.status == "unavailable" for r in ordered) else "insufficient_evidence")
    difference, cheaper_id, citations = None, None, []
    text = {"invalid_answer": INVALID, "unavailable": UNAVAILABLE, "insufficient_evidence": INSUFFICIENT}.get(status, "")
    if status in {"answered", "partial"}:
        rendered = {}
        for i, row in enumerate(supported, 1):
            validate_passages(row.task, [row.evidence], manifest)
            draft = RagAnswerDraft(status="answered", selections=[row.selection])
            block, refs = render_document_answer(draft, [row.evidence], manifest)
            label = f"Source {i}"
            rendered[row.task.task_id] = block.replace("Source: Source 1 — ", f"Source: {label} — ")
            citations.append(DocumentCitation.model_validate({**refs[0].model_dump(), "label": label}))
        menus = [r for r in ordered if r.task.criterion == "menu_item_price"]
        comparable = len(menus) == 2 and all(r.status == "supported" and r.price for r in menus)
        comparable = comparable and menus[0].price.currency == menus[1].price.currency and menus[0].price.unit == menus[1].price.unit
        description = document_description(manifest, {t.restaurant_id for t in plan.tasks})
        lines = [f"Answered {len(supported)} of {len(ordered)} requested parts using the {description}.", "", "## Menu prices"]
        for criterion in ("menu_item_price", "cancellation_policy"):
            if criterion == "cancellation_policy":
                if comparable:
                    a, b = (r.price.amount for r in menus)
                    difference = abs(a-b)
                    cheaper_id = None if a == b else menus[0 if a < b else 1].task.restaurant_id
                    name = next(r.task.restaurant_name for r in menus if r.task.restaurant_id == cheaper_id) if cheaper_id else None
                    from src.application.document_rag.native_menu import unit_suffix
                    suffix = unit_suffix(menus[0].price.unit)
                    lines.extend(["", f"{safe_markdown(name)}'s listed price is RM{difference} lower{suffix}." if name
                                  else f"The listed prices are equal{suffix}."])
                elif len(menus) == 2:
                    lines.extend(["", "A price difference cannot be calculated without two verified prices in matching currency and serving units."])
                lines.extend(["", "## Cancellation policies"])
            for row in ordered:
                if row.task.criterion == criterion:
                    lines.extend(["", f"### {safe_markdown(row.task.restaurant_name)}", "",
                                  rendered[row.task.task_id] if row.status == "supported" else REASONS[row.reason]])
        text = "\n".join(lines)
    elif status in {"unavailable", "insufficient_evidence"}:
        text += "\n\n" + "\n".join(f"{safe_markdown(r.task.restaurant_name)} — {r.task.criterion}: {REASONS[r.reason]}" for r in ordered)
    return MultipartResult(plan=plan, rows=ordered, status=status, supported=len(supported), difference=difference,
                           cheaper_id=cheaper_id, text=text, citations=tuple(citations))
