"""Bounded discovery joins real document coverage to actual external search results."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import re
from urllib.parse import urlsplit

from langchain_core.messages import AIMessage, HumanMessage

from src.config import settings
from src.domain.document_rag import canonical_text, public_source_url
from src.infrastructure.model import extract_text_content
from src.infrastructure.rag_observability import rag_span


def is_coverage_discovery_request(question):
    text = canonical_text(question).casefold()
    return bool(re.search(r"\b(find|discover|recommend)\b", text) and re.search(r"\brestaurants?\b", text)
                and re.search(r"\b(document collection|document coverage|knowledge base)\b", text))


def discovery_filters(question):
    text = canonical_text(question).rstrip(".?!")
    match = re.fullmatch(r"find (?:two|2) ([\w -]{1,50}) restaurants in ([\w -]{1,80}) that have menus in your document collection", text, re.I)
    return (match[1].casefold(), match[2].casefold()) if match else None


def online_match(venue, result):
    """A matching official-domain result verifies identity, not every catalog fact."""
    if result.status == "error":
        return None
    host = urlsplit(venue.website).hostname.removeprefix("www.")
    urls = []
    aliases = {canonical_text(n).casefold() for n in (venue.name, *venue.aliases)}
    for record in result.restaurants:
        location = canonical_text(" ".join(x for x in (record.city, record.address) if x)).casefold()
        if canonical_text(record.name).casefold() in aliases and canonical_text(venue.city).casefold() in location and record.website:
            urls.append(record.website)
    # Generic pages stay identified as online sources, never fabricated place records.
    urls.extend(source.get("url", "") for source in result.web_sources)
    for url in urls:
        try:
            public_source_url(url)
            if urlsplit(url).hostname.removeprefix("www.") == host:
                return url
        except ValueError:
            continue
    return None


@dataclass(frozen=True)
class DiscoveryResult:
    text: str
    verified_count: int = 0
    search_attempts: int = 0
    generation_id: str | None = None


async def discover_document_venues(question, *, retriever=None, search=None, remaining_tools=4, attempts=None):
    from src.application.document_rag.workflow import make_retriever, safe_markdown
    from src.application.document_rag.comparison_workflow import close_retriever
    from src.application.orchestrator.workflow.agents.restaurant_data_agent import run_restaurant_data_agent
    filters = discovery_filters(question)
    if filters is None:
        return DiscoveryResult("Please ask for two restaurants in one city and cuisine that have menus in the document collection.")
    owned = retriever is None
    retriever = retriever or make_retriever()
    try:
        manifest = await asyncio.to_thread(retriever.pin)
    finally:
        if owned:
            close_retriever(retriever)
    cuisine, city = filters
    menu_ids = {c.restaurant_id for c in manifest.chunks if c.document_type == "menu"}
    venues = [r for r in manifest.restaurants if not r.fictional and r.restaurant_id in menu_ids
              and canonical_text(r.cuisine or "").casefold() == cuisine and canonical_text(r.city or "").casefold() == city]
    if len(venues) != 2:
        return DiscoveryResult("The active collection does not identify exactly two real restaurants with menu coverage for that city and cuisine. Please narrow the request or ask about a named restaurant.", generation_id=manifest.generation_id)
    if remaining_tools < 2:
        return DiscoveryResult("The search budget for this turn is exhausted. Please start a new request.", generation_id=manifest.generation_id)
    search = search or run_restaurant_data_agent
    matches = []
    attempts = attempts if attempts is not None else []
    for venue in venues:
        with rag_span("rag.discovery.search", {"rag.restaurant":venue.restaurant_id, "rag.generation":manifest.generation_id}):
            try:
                # Consume a slot before sending: failures/cancellations are attempts.
                official_host = urlsplit(public_source_url(venue.website)).hostname.removeprefix("www.")
                attempts.append(venue.restaurant_id)
                result = await search(query=f"{venue.name} {venue.city} official website site:{official_host}", cuisine=venue.cuisine, location=venue.city, limit=5)
                matches.append(online_match(venue, result))
            except asyncio.CancelledError:
                raise
            except Exception:
                matches.append(None)
    verified = [(venue, url) for venue, url in zip(venues, matches) if url]
    if not verified:
        return DiscoveryResult("The collection has menu-covered venues, but I couldn't verify their official websites through online search. I cannot present them as successfully discovered online.", 0, 2, manifest.generation_id)
    lines = [f"Verified {len(verified)} of 2 document-covered {safe_markdown(venues[0].cuisine)} restaurants in {safe_markdown(venues[0].city)} through online search.",
             "This shortlist is limited to the document collection; it is not a city-wide ranking."]
    for index, (venue, url) in enumerate(verified, 1):
        lines.extend(["", f"### {index}. {safe_markdown(venue.name)}", f"{safe_markdown(venue.cuisine)} — {safe_markdown(venue.city)}",
                      f"[Online source: official website]({url})", "Original menu documents are available for follow-up questions."])
    if len(verified) < 2:
        lines.append("Some document-covered venues could not be verified online.")
    return DiscoveryResult("\n".join(lines), len(verified), 2, manifest.generation_id)


async def coverage_discovery_node(state, config):
    attempts = []
    question = next((extract_text_content(m.content) for m in reversed(state.get("messages", [])) if isinstance(m, HumanMessage)), "")
    if not settings.DOCUMENT_RAG_ENABLED or not settings.DOCUMENT_REAL_SOURCES_ENABLED:
        result = DiscoveryResult("Discovery from real source documents is currently disabled.")
    else:
        try:
            async with asyncio.timeout(settings.RAG_REQUEST_TIMEOUT_SECONDS):
                result = await discover_document_venues(question, remaining_tools=4-state.get("tool_call_count", 0), attempts=attempts)
        except asyncio.CancelledError:
            raise
        except Exception:
            result = DiscoveryResult("Document-covered restaurant discovery is temporarily unavailable.")
    return {"messages":AIMessage(content=result.text), "tool_call_count":state.get("tool_call_count",0)+len(attempts),
            "made_tool_calls":bool(attempts), "coverage_discovery_requested":False}
