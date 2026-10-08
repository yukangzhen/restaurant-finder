"""
Restaurant Explorer Agent - Browser-based restaurant search.

This agent uses AWS Bedrock AgentCore Browser tools to search for restaurants
on the web, extracting and structuring the results using an LLM.

Architecture:
- Direct browser tool invocation (not ReAct) for reliable session control
- LLM-based extraction of structured data from raw web content
- One unique browser session per operation with inherited trace callbacks
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from src.domain.models import RestaurantSearchResult
from src.domain.restaurant_results import parse_restaurant, parse_search_result
from src.domain.prompts import RESTAURANT_EXTRACTION_PROMPT
from src.infrastructure.browser import create_browser_operation, close_browser_operation
from src.infrastructure.model import get_model, ModelType, extract_text_content


# =============================================================================
# Constants
# =============================================================================

SEARCH_ENGINE_URL = "https://duckduckgo.com"
SEARCH_TIMEOUT_MS = 15000
MAX_TEXT_FOR_EXTRACTION = 8000


# =============================================================================
# Restaurant Parsing
# =============================================================================

def parse_json_results(json_text: str, query: str) -> RestaurantSearchResult:
    """
    Parse JSON text into a RestaurantSearchResult.

    Args:
        json_text: JSON string containing restaurant array.
        query: Original search query.

    Returns:
        RestaurantSearchResult with parsed restaurants or empty result.
    """
    try:
        json_match = re.search(r'\[[\s\S]*\]', json_text)
        if json_match:
            data = json.loads(json_match.group())
            if isinstance(data, list):
                return parse_search_result(
                    {"restaurants": data, "data_source": "browser"},
                    query,
                    default_data_source="browser",
                )
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to parse browser extraction (error_type={})", type(e).__name__)

    return RestaurantSearchResult(
        query=query,
        total_results=0,
        restaurants=[],
        data_source="browser",
        notes="No verified restaurant records were extracted from the web results.",
        status="empty",
    )


# =============================================================================
# LLM Extraction
# =============================================================================

async def extract_restaurants_from_text(raw_text: str, query: str) -> str:
    """
    Use an LLM to extract structured restaurant data from raw web content.

    Args:
        raw_text: Raw text extracted from browser.
        query: Original search query for context.

    Returns:
        JSON string containing extracted restaurant data.
    """
    try:
        model = get_model(temperature=0.1, model_type=ModelType.EXTRACTION)

        messages = [
            SystemMessage(content=RESTAURANT_EXTRACTION_PROMPT.prompt),
            HumanMessage(
                content=(
                    f"<search_query>{query}</search_query>\n\n"
                    f"<web_content>\n{raw_text[:MAX_TEXT_FOR_EXTRACTION]}\n</web_content>"
                )
            ),
        ]

        response = await model.ainvoke(messages)
        result = extract_text_content(response.content)

        logger.info(f"LLM extraction completed, response length: {len(result)}")
        return result

    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return "[]"


# =============================================================================
# Browser Operations
# =============================================================================

async def search_web(query: str, tools: dict, config: dict) -> str:
    """
    Perform a web search using browser tools.

    Args:
        query: Search query.
        config: Browser config with thread_id for session isolation.

    Returns:
        Combined raw text from search results page.
    """
    results = []

    # Build search URL
    search_query = f"{query} restaurants reviews"
    search_url = f"{SEARCH_ENGINE_URL}/?q={search_query.replace(' ', '+')}&ia=web"

    # Navigate to search engine
    logger.info(f"Navigating to: {search_url}")
    await tools["navigate_browser"].ainvoke({"url": search_url}, config=config)

    # Wait for results to load
    logger.info("Waiting for search results...")
    await tools["wait_for_element"].ainvoke(
        {
            "selector": "[data-testid='result'], .result, .results, article",
            "timeout": SEARCH_TIMEOUT_MS,
            "state": "visible",
        },
        config=config,
    )

    # Extract page content
    logger.info("Extracting page content...")
    page_text = await tools["extract_text"].ainvoke({}, config=config)
    results.append(str(page_text))

    # Extract links for additional context
    logger.info("Extracting hyperlinks...")
    links = await tools["extract_hyperlinks"].ainvoke({}, config=config)
    results.append(f"Links found: {links}")

    return "\n\n".join(results)


# =============================================================================
# Main Entry Point
# =============================================================================

async def run_restaurant_explorer(
    query: str,
    parent_config: dict | None = None,
) -> RestaurantSearchResult:
    """
    Search for restaurants using browser automation and LLM extraction.

    This is the main entry point for the restaurant explorer agent. It:
    1. Opens a browser session with DuckDuckGo
    2. Extracts raw text from search results
    3. Uses an LLM to parse the text into structured restaurant data

    Args:
        query: Search query describing restaurants to find.
            Examples:
            - "Italian restaurants in San Francisco"
            - "Vegetarian Thai food under $30"
            - "Fine dining with outdoor seating in NYC"
        Each invocation creates and closes its own unique browser session.

    Returns:
        RestaurantSearchResult: Structured search results.
    """
    toolkit, tools, config = create_browser_operation(parent_config)
    effective_thread_id = config["configurable"]["thread_id"]

    logger.info(f"Starting restaurant search: '{query}' (thread_id={effective_thread_id})")

    try:
        # Step 1: Search the web
        raw_content = await search_web(query, tools, config)
        logger.info(f"Browser search completed, content length: {len(raw_content)}")

        # Step 2: Extract structured data using LLM
        extracted_json = await extract_restaurants_from_text(raw_content, query)

        # Step 3: Parse into result model
        return parse_json_results(extracted_json, query)

    except Exception as e:
        logger.error("Restaurant search failed (error_type={})", type(e).__name__)
        return RestaurantSearchResult(
            query=query,
            total_results=0,
            restaurants=[],
            data_source="browser",
            notes="Browser search could not be completed.",
            status="error",
            error_code="browser_search_failed",
        )

    finally:
        # Always cleanup browser session
        try:
            await close_browser_operation(toolkit)
            logger.info(f"Browser session cleaned up (thread_id={effective_thread_id})")
        except Exception as cleanup_error:
            logger.warning(f"Browser cleanup failed: {cleanup_error}")
