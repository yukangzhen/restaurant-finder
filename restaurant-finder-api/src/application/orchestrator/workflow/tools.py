import asyncio
import json
import re
import time
from typing import Annotated, Any, Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from loguru import logger

from src.application.orchestrator.workflow.agents.restaurant_explorer_agent import (
    run_restaurant_explorer,
)
from src.application.orchestrator.workflow.agents.restaurant_data_agent import (
    run_restaurant_data_agent,
)
from src.application.orchestrator.workflow.agents.restaurant_research_agent import (
    run_restaurant_research,
)
from src.config import settings
from src.domain.models import RestaurantSearchResult
from src.infrastructure.memory import get_memory_instance
from src.infrastructure.observability import get_observability_manager


@tool
async def restaurant_explorer_tool(
    query: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
    limit: int = 5,
) -> str:
    """
    BACKUP ONLY - Browser-based web search for restaurants.

    This tool is SLOW. Use it only for requests about "trending", "new", or
    "latest" restaurants. The primary search tool handles result-shortfall fallback.

    DO NOT use this for normal restaurant searches - use restaurant_data_tool instead.

    Args:
        query: Search request with cuisine, location, price, dietary needs.

    Returns:
        JSON with restaurants (name, cuisine, rating, price, address, features).
    """
    requested_count = _requested_result_count(query, limit)
    result: RestaurantSearchResult = await run_restaurant_explorer(
        query=query,
        parent_config=config,
    )
    result = result.model_copy(
        update={
            "restaurants": result.restaurants[:requested_count],
            "total_results": min(result.total_results, requested_count),
        }
    )
    return result.model_dump_json(indent=2)


@tool
async def restaurant_data_tool(
    query: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
    cuisine: str = "",
    location: str = "",
    price_range: str = "",
    dietary_restrictions: list[str] = None,
    limit: int = 5,
) -> str:
    """
    PRIMARY TOOL - ALWAYS use this first for ANY restaurant search.

    Fast, reliable restaurant search via Google Local API. Returns structured
    data with ratings, reviews, addresses, phone numbers, hours, and more.

    IMPORTANT: This is your go-to tool for all restaurant searches. When browser
    tools are enabled, it automatically tries browser search only if verified
    results fall below min(4, the requested number).

    Args:
        query: What restaurants to find (e.g., "best pizza near Times Square").
        cuisine: Cuisine type (Italian, Japanese, etc.).
        location: City or area to search (REQUIRED for best results).
        price_range: "$", "$$", "$$$", or "$$$$".
        dietary_restrictions: List like ["Vegetarian", "Gluten-Free"].
        limit: Max results (1-10).

    Returns:
        JSON with restaurants including ratings, addresses, hours, phone, and more.
    """
    requested_count = _requested_result_count(query, limit)
    result: RestaurantSearchResult = await run_restaurant_data_agent(
        query=query,
        cuisine=cuisine,
        location=location,
        price_range=price_range,
        dietary_restrictions=dietary_restrictions or [],
        limit=requested_count,
    )
    fallback_threshold = min(4, requested_count)
    if settings.ENABLE_BROWSER_TOOLS and result.total_results < fallback_threshold:
        browser_result = await run_restaurant_explorer(query=query, parent_config=config)
        result = _merge_search_results(result, browser_result, requested_count)
    return result.model_dump_json(indent=2)


def _requested_result_count(query: str, tool_limit: int | None) -> int:
    """Honor an explicit count in the request; otherwise use the tool default."""
    count = r"(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)"
    explicit_patterns = (
        rf"\b(?:give|show|find|recommend|suggest|list)\s+(?:me\s+)?(?:exactly\s+)?{count}\s+(?:restaurants|places|options|recommendations)\b",
        rf"\btop\s+{count}\s+(?:restaurants|places|options|recommendations)\b",
    )
    words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }
    for pattern in explicit_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            found = match.group(1).lower()
            if found in words:
                return words[found]
            return min(max(1, int(found)), 10)
    try:
        return min(max(1, int(tool_limit or 5)), 10)
    except (TypeError, ValueError):
        return 5


def _merge_search_results(
    primary: RestaurantSearchResult,
    fallback: RestaurantSearchResult,
    requested_count: int,
) -> RestaurantSearchResult:
    """Combine structured results while keeping generic pages as sources."""
    restaurants = []
    seen = set()
    for restaurant in [*primary.restaurants, *fallback.restaurants]:
        identity = (restaurant.name.casefold(), (restaurant.address or "").casefold())
        if identity not in seen:
            seen.add(identity)
            restaurants.append(restaurant)
        if len(restaurants) >= requested_count:
            break

    source = primary.data_source
    if fallback.total_results:
        source = f"{primary.data_source}+browser"
    if restaurants:
        status, error_code = "success", None
    elif primary.status == "error" and fallback.status == "error":
        status, error_code = "error", primary.error_code or fallback.error_code
    else:
        status, error_code = "empty", None

    notes = primary.notes
    if fallback.total_results:
        notes = "Structured browser results added after the primary search returned too few records."
    elif primary.total_results < min(4, requested_count):
        notes = "The search returned fewer verified restaurant records than requested."

    return primary.model_copy(
        update={
            "restaurants": restaurants,
            "total_results": len(restaurants),
            "data_source": source,
            "status": status,
            "error_code": error_code,
            "web_sources": [*primary.web_sources, *fallback.web_sources],
            "notes": notes,
        }
    )


@tool
async def memory_retrieval_tool(
    query: str,
    memory_types: list[Literal["preferences", "facts", "summaries"]],
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """
    Retrieve user's stored preferences, facts, or conversation summaries.
    Use for personalization before making recommendations.

    Args:
        query: Search query for semantic matching.
        memory_types: List of types to retrieve:
            - "preferences": Dietary, cuisine, price, location preferences
            - "facts": Details from past conversations
            - "summaries": Current session context

    Returns:
        JSON with memories organized by type.
    """
    configurable = config.get("configurable", {}) if config else {}
    actor_id = configurable.get("actor_id", "user:default")
    session_id = configurable.get("thread_id", "default_session")

    logger.debug(f"Memory retrieval requested for categories={memory_types}")

    observability = get_observability_manager()
    start_time = time.monotonic()
    try:
        memory = get_memory_instance()
        retrieved = await asyncio.to_thread(
            memory.retrieve_specific_memories,
            query=query,
            actor_id=actor_id,
            session_id=session_id,
            memory_types=memory_types,
            top_k=5,
        )

        formatted_results: dict[str, Any] = {}
        for mem_type, items in retrieved.memories.items():
            formatted_results[mem_type] = [_memory_record_text(item) for item in items]
            observability.record_memory_operation(
                "retrieve",
                success=mem_type not in retrieved.errors,
                duration_ms=(time.monotonic() - start_time) * 1000,
                category=mem_type,
            )
        for mem_type in memory_types:
            formatted_results.setdefault(mem_type, [])
        if retrieved.errors:
            formatted_results["errors"] = retrieved.errors

        result_json = json.dumps(formatted_results, indent=2)

        logger.debug(f"Memory retrieval complete: {len(result_json)} chars")
        return result_json

    except Exception as e:
        logger.error(f"Memory retrieval failed: {type(e).__name__}")
        observability.record_memory_operation(
            "retrieve", success=False,
            duration_ms=(time.monotonic() - start_time) * 1000,
        )
        return json.dumps(
            {
                "errors": {"request": type(e).__name__},
                "preferences": [],
                "facts": [],
                "summaries": [],
            }
        )


def _memory_record_text(record: dict[str, Any]) -> str:
    """Return the human-readable text from an AgentCore memory record."""
    content = record.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text
    return ""


@tool
async def restaurant_research_tool(
    restaurant_name: str,
    location: str,
    research_topics: list[str] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
) -> str:
    """
    FOLLOW-UP ONLY - Deep research on ONE specific restaurant.

    Use ONLY when user asks for more details about a restaurant that was already
    mentioned or recommended. Examples: "Tell me more about X", "What's on the
    menu at X?", "Does X have parking?", "How do I make a reservation at X?"

    DO NOT use this for initial restaurant searches - use restaurant_data_tool instead.

    Args:
        restaurant_name: Restaurant to research (must be a specific restaurant).
        location: City or area.
        research_topics: Optional topics: "menu", "reviews", "reservations",
                        "parking", "events", "contact", "directions".

    Returns:
        JSON with detailed research findings.
    """
    logger.debug(f"Restaurant research: name='{restaurant_name}', location='{location}', topics={research_topics}")

    try:
        result = await run_restaurant_research(
            restaurant_name=restaurant_name,
            location=location,
            research_topics=research_topics,
            parent_config=config,
        )

        logger.debug("Restaurant research complete")
        return json.dumps(result, indent=2)

    except Exception as error:
        logger.error("Restaurant research failed (error_type={})", type(error).__name__)
        return json.dumps({
            "restaurant_name": restaurant_name,
            "error": "Research could not be completed.",
            "error_code": "browser_research_failed",
            "research_summary": "I couldn't verify additional details from web search results.",
        })


# Core tools (always available)
_CORE_TOOLS = [
    restaurant_data_tool,       # MCP Gateway to Lambda (SearchAPI web search)
    memory_retrieval_tool,      # On-demand memory retrieval
]

# Browser-based tools (optional)
_BROWSER_TOOLS = [
    restaurant_explorer_tool,   # Browser-based web search for finding restaurants
    restaurant_research_tool,   # Browser-based detailed research on specific restaurant
]


def get_orchestrator_tools(include_browser_tools: bool | None = None) -> list:
    """
    Get the list of tools available to the orchestrator.

    Args:
        include_browser_tools: Override for browser tools inclusion.
                              If None, uses ENABLE_BROWSER_TOOLS from config.

    Returns:
        List of tools for the orchestrator to use.
    """
    use_browser = include_browser_tools if include_browser_tools is not None else settings.ENABLE_BROWSER_TOOLS

    tools = list(_CORE_TOOLS)

    if use_browser:
        tools.extend(_BROWSER_TOOLS)
        logger.info("Browser tools enabled")
    else:
        logger.info("Browser tools disabled")

    return tools

