"""Pure, bounded document follow ups using only approved server context."""
from __future__ import annotations

import json
import re
from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from src.domain.document_conversation import (
    DocumentContextDraft, DocumentConversationContext, DocumentFollowupDraft,
    FollowupResolution, PendingDocumentFollowup,
)
from src.domain.document_rag import RestaurantEntry, canonical_text, digest

CLARIFY = "Please ask a complete document question naming the fictional restaurant or restaurants and, for prices, the menu item."


def read_contract(model, value):
    """Checkpoint tuples arrive as JSON arrays; strict JSON validation preserves types."""
    if isinstance(value, model):
        value = value.model_dump(mode="json")
    return model.model_validate_json(json.dumps(value, ensure_ascii=False))


def catalog_entries(catalog=None):
    if catalog is None:
        from src.application.document_rag.retrieval import router_catalog
        catalog = router_catalog()
    return [RestaurantEntry.model_validate(r) for r in getattr(catalog, "restaurants", catalog)]


def _owner(config):
    from src.application.orchestrator.identity import resolve_request_identity
    values = config.get("configurable", {})
    if not values.get("thread_id"):
        raise ValueError("Context requires a conversation identity")
    identity = resolve_request_identity(values["thread_id"], values.get("actor_id"))
    return digest(identity.actor_id), digest(identity.conversation_id)


def _previous_pair(messages):
    current = next((i for i in range(len(messages)-1, -1, -1) if isinstance(messages[i], HumanMessage)), -1)
    prefix = messages[:current] if current >= 0 else []
    human = next((i for i in range(len(prefix)-1, -1, -1) if isinstance(prefix[i], HumanMessage)), -1)
    assistant = next((m for m in reversed(prefix[human+1:]) if isinstance(m, AIMessage)), None)
    if human < 0 or assistant is None or assistant.tool_calls:
        return None
    return prefix[human].id, assistant.id


def _read_owned(model, value, config, entries):
    parsed = read_contract(model, value)
    if (parsed.actor_digest, parsed.thread_digest) != _owner(config):
        raise ValueError("Context owner differs")
    targets = parsed.restaurant_ids if isinstance(parsed, DocumentConversationContext) else parsed.candidate_ids
    if not set(targets) <= {r.restaurant_id for r in entries}:
        raise ValueError("Context target is outside catalog")
    return parsed


def eligible_context(state, config, catalog=None):
    try:
        context = _read_owned(DocumentConversationContext, state.get("rag_approved_context"), config, catalog_entries(catalog))
        if _previous_pair(state.get("messages", [])) == (context.human_message_id, context.ai_message_id):
            return context
    except (ValueError, TypeError):
        pass
    return None


def _eligible_pending(state, config, entries):
    try:
        context = _read_owned(DocumentConversationContext, state.get("rag_approved_context"), config, entries)
        pending = _read_owned(PendingDocumentFollowup, state.get("rag_approved_followup"), config, entries)
        if (pending.context_digest != context.payload_digest or pending.candidate_ids != context.restaurant_ids
                or _previous_pair(state.get("messages", [])) != (pending.human_message_id, pending.ai_message_id)):
            return None
        # The retained producer must still precede the approved clarification.
        messages = state.get("messages", [])
        ids = [m.id for m in messages]
        if (context.human_message_id not in ids or context.ai_message_id not in ids
                or ids.index(context.human_message_id) >= ids.index(context.ai_message_id)
                or ids.index(context.ai_message_id) >= ids.index(pending.human_message_id)):
            return None
        return pending
    except (ValueError, TypeError):
        return None


def _alias_id(text, entries):
    values = {r.restaurant_id for r in entries for alias in [r.name, *r.aliases]
              if canonical_text(alias).casefold() == text}
    return next(iter(values)) if len(values) == 1 else None


def _name(rid, entries):
    restaurant = next(r for r in entries if r.restaurant_id == rid)
    return restaurant.aliases[0] if restaurant.aliases else restaurant.name


def effective_question(operation, targets, item, entries):
    names = [_name(rid, entries) for rid in targets]
    if operation in {"cancellation_fee", "cancellation_policy"}:
        return (f"According to {names[0]}'s policy, quote the complete Reservations and cancellation policy, "
                "including the free-cancellation window and late-cancellation fee.")
    if operation == "menu_item_price":
        return f"According to {names[0]}'s menu, what is the {item} price?"
    if operation == "price_comparison":
        return f"Compare {item} prices at {names[0]} and {names[1]}."
    if len(names) == 1:
        return f"For {names[0]}, what is the {item} price and cancellation policy?"
    return f"Compare {item} prices at {names[0]} and {names[1]}, and explain both restaurants' cancellation policies."


def _resolved(operation, targets, item, reason, entries):
    question = effective_question(operation, targets, item, entries)
    if operation == "price_comparison":
        from src.application.document_rag.comparison import plan_comparison
        plan = plan_comparison(question, SimpleNamespace(restaurants=entries, generation_id="0" * 64))
        if plan is None or plan.restaurant_ids != targets or canonical_text(plan.item).casefold() != item:
            return _clarify("unsupported")
    elif operation == "price_and_policy":
        from src.application.document_rag.multipart import compile_multipart_request
        plan = compile_multipart_request(question, entries)
        if (plan is None or tuple(dict.fromkeys(t.restaurant_id for t in plan.tasks)) != targets
                or {t.item for t in plan.tasks if t.item} != {item}):
            return _clarify("unsupported")
    return FollowupResolution(decision="resolved", reason=reason, operation=operation,
                              restaurant_ids=targets, item=item, effective_question=question)


def _clarify(reason, operation=None, text=CLARIFY, pending=None):
    return FollowupResolution(decision="clarify", reason=reason, operation=operation,
                              clarification=text, pending=pending)


def resolve_followup(question, state, config, catalog=None):
    entries = catalog_entries(catalog)
    text = canonical_text(question).replace("\u2019", "'").casefold()
    continuation = bool(re.match(r"^(?:and\s+)?(?:what about|what is)\s+(?:its|their|both restaurants)\b", text)
                        or re.match(r"^(?:and\s+)?(?:which is cheaper|what is the price difference)\b", text)
                        or re.match(r"^(?:and\s+)?what about .+?'s cancellation (fee|policy)\b", text))
    if len(question) > 1000 or any(not c.isprintable() for c in question):
        return _clarify("unsupported") if continuation else FollowupResolution(decision="not_applicable", reason="not_applicable")
    text = re.sub(r"^[Aa]nd\s+", "", text)
    text = re.sub(r"[?.]$", "", text).strip()
    rid = _alias_id(text, entries)
    pending = _eligible_pending(state, config, entries)
    if rid:
        if pending and rid in pending.candidate_ids:
            return _resolved(pending.operation, (rid,), pending.item, "resumed", entries)
        return _clarify("expired_clarification", text=f"What would you like to know from {_name(rid, entries)}'s documents?")
    if pending:
        # A multiple-name reply is not a complete independent question.
        leftovers = text
        for alias in sorted((canonical_text(a).casefold() for r in entries for a in [r.name, *r.aliases]), key=len, reverse=True):
            leftovers = re.sub(r"(?<!\w)"+re.escape(alias)+r"(?!\w)", "", leftovers)
        if leftovers != text and re.fullmatch(r"[\s,]*(?:and|or)?[\s,]*", leftovers):
            return _clarify("unsupported")

    explicit = re.fullmatch(r"what about (.+?)'s cancellation (fee|policy)", text)
    if explicit:
        rid = _alias_id(explicit[1], entries)
        if rid is None:
            return _clarify("unknown_venue")
        return _resolved("cancellation_fee" if explicit[2] == "fee" else "cancellation_policy", (rid,), None, "explicit_venue", entries)
    if re.match(r"what about .+?'s cancellation (fee|policy)\b", text):
        return _clarify("unsupported")

    # Complete existing forms retain their original routing and admission.
    from src.application.document_rag.comparison import plan_comparison
    from src.application.document_rag.multipart import compile_multipart_request
    if (plan_comparison(question, SimpleNamespace(restaurants=entries, generation_id="0" * 64)) is not None
            or compile_multipart_request(question, entries) is not None):
        return FollowupResolution(decision="not_applicable", reason="not_applicable")
    if any(
            re.search(r"(?<!\w)"+re.escape(canonical_text(alias).casefold())+r"(?!\w)", text)
            for r in entries for alias in [r.name, *r.aliases]) and not re.search(r"\b(its|their|both)\b", text):
        return FollowupResolution(decision="not_applicable", reason="not_applicable")

    forms = {"what about its cancellation fee": "cancellation_fee", "what is its cancellation fee": "cancellation_fee",
             "what about its cancellation policy": "cancellation_policy", "what is its cancellation policy": "cancellation_policy",
             "which is cheaper": "price_comparison", "what is the price difference": "price_comparison",
             "what about its price": "menu_item_price", "what is its price": "menu_item_price",
             "what about its price and cancellation policy": "price_and_policy",
             "what about both restaurants' prices and cancellation policies": "both"}
    operation = forms.get(text)
    if operation is None:
        document_history = bool(state.get("rag_approved_context") or state.get("rag_approved_followup")
                                or state.get("last_approved_intent") == "document_qa")
        return _clarify("unsupported") if continuation and document_history else FollowupResolution(decision="not_applicable", reason="not_applicable")
    context = eligible_context(state, config, entries)
    if context is None:
        return _clarify("invalid_context" if state.get("rag_approved_context") else "no_context",
                        "price_and_policy" if operation == "both" else operation)
    needs_item = operation in {"menu_item_price", "price_comparison", "price_and_policy", "both"}
    if needs_item and context.item is None:
        return _clarify("missing_item", "price_and_policy" if operation == "both" else operation)
    if operation in {"price_comparison", "both"}:
        if len(context.restaurant_ids) != 2:
            return _clarify("unsupported", "price_and_policy" if operation == "both" else operation)
        return _resolved("price_and_policy" if operation == "both" else operation,
                         context.restaurant_ids, context.item, "resolved", entries)
    item = context.item if needs_item else None
    if len(context.restaurant_ids) == 2:
        pending = DocumentFollowupDraft(operation=operation, candidate_ids=context.restaurant_ids,
                                        item=item, context_digest=context.payload_digest)
        names = [_name(rid, entries) for rid in context.restaurant_ids]
        return _clarify("ambiguous_venue", operation,
                        f"Which restaurant's documents should I use: {names[0]} or {names[1]}?", pending)
    return _resolved(operation, context.restaurant_ids, item, "resolved", entries)


def latest_question(state):
    from src.infrastructure.model import extract_text_content
    return next((extract_text_content(m.content) for m in reversed(state.get("messages", [])) if isinstance(m, HumanMessage)), "")


def checked_resolution(state, config):
    value = state.get("rag_followup_resolution")
    if value is None:
        return None
    resolution = read_contract(FollowupResolution, value)
    if resolution != resolve_followup(latest_question(state), state, config):
        raise ValueError("Resolution differs from admitted continuation")
    return resolution


def context_draft(targets, item, mode, generation):
    return DocumentContextDraft(restaurant_ids=tuple(targets), item=canonical_text(item).casefold() if item else None,
                                 origin_mode=mode, generation_id=generation)


def _seal(model, draft, config, human, assistant):
    actor, thread = _owner(config)
    payload = {**draft.model_dump(mode="json"), "schema_version": 1, "actor_digest": actor, "thread_digest": thread,
               "human_message_id": human.id, "ai_message_id": assistant.id}
    return read_contract(model, {**payload, "payload_digest": digest(payload)}).model_dump(mode="json")


def approved_context_update(state, config, replacement, unchanged, references, coverage):
    """Only the output gate calls this after moderation and citation validation."""
    update = {"rag_pending_context": None, "rag_pending_followup": None,
              "rag_approved_context": None, "rag_approved_followup": None, "rag_approved_scope": None}
    if not unchanged or state.get("intent") != "document_qa":
        return update
    human = next((m for m in reversed(state.get("messages", [])) if isinstance(m, HumanMessage)), None)
    resolution = checked_resolution(state, config)
    if state.get("rag_status") == "clarify" and state.get("rag_pending_followup"):
        draft = read_contract(DocumentFollowupDraft, state["rag_pending_followup"])
        context = eligible_context(state, config)
        if (context is None or resolution is None or draft != resolution.pending
                or replacement.content != resolution.clarification):
            raise ValueError("Clarification differs from admitted continuation")
        update["rag_approved_context"] = context.model_dump(mode="json")
        update["rag_approved_followup"] = _seal(PendingDocumentFollowup, draft, config, human, replacement)
        return update
    if state.get("rag_status") not in {"answered", "partial"} or not references:
        return update
    draft = read_contract(DocumentContextDraft, state.get("rag_pending_context"))
    mode = state.get("rag_mode")
    if draft.origin_mode != mode or draft.generation_id != state.get("rag_generation") or any(
            c.generation_id != draft.generation_id for c in references):
        raise ValueError("Context differs from approved sources")
    entries = catalog_entries()
    if not set(draft.restaurant_ids) <= {r.restaurant_id for r in entries}:
        raise ValueError("Context target is outside catalog")
    if resolution and resolution.decision == "resolved":
        if draft.restaurant_ids != resolution.restaurant_ids or draft.item != resolution.item:
            raise ValueError("Context differs from resolved request")
    elif mode == "single":
        if draft.restaurant_ids != (state.get("rag_pending_scope"),) or draft.item is not None:
            raise ValueError("Context differs from single request")
    elif mode == "comparison":
        from src.application.document_rag.comparison import plan_comparison
        plan = plan_comparison(latest_question(state), SimpleNamespace(restaurants=entries, generation_id=draft.generation_id))
        if plan is None or plan.restaurant_ids != draft.restaurant_ids or canonical_text(plan.item).casefold() != draft.item:
            raise ValueError("Context differs from comparison request")
    else:
        from src.application.document_rag.multipart import compile_multipart_request
        plan = compile_multipart_request(latest_question(state), entries)
        if (plan is None or tuple(dict.fromkeys(t.restaurant_id for t in plan.tasks)) != draft.restaurant_ids
                or {t.item for t in plan.tasks if t.item} != {draft.item}):
            raise ValueError("Context differs from multipart request")
    if mode == "multipart" and (coverage is None or tuple(dict.fromkeys(t.restaurant_id for t in coverage.tasks)) != draft.restaurant_ids):
        raise ValueError("Context differs from coverage")
    update["rag_approved_context"] = _seal(DocumentConversationContext, draft, config, human, replacement)
    if len(draft.restaurant_ids) == 1:
        update["rag_approved_scope"] = draft.restaurant_ids[0]
    return update
