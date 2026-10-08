"""Restaurant search through the AgentCore Gateway MCP tool."""

from __future__ import annotations

from typing import Any

from loguru import logger

from src.domain.models import Restaurant, RestaurantSearchResult
from src.domain.restaurant_results import (
    RestaurantDataError,
    normalize_restaurant_response,
    parse_restaurant,
    parse_search_result as _parse_search_result,
    safe_search_error,
)
from src.infrastructure.mcp_client import get_mcp_client, is_mcp_configured


SEARCH_RESTAURANTS_TOOL = "search_restaurants"


async def call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Invoke the gateway tool and normalize MCP/Lambda response encodings."""
    try:
        client = get_mcp_client()
        tools = await client.get_tools()
        target_tool = next(
            (
                tool
                for tool in tools
                if tool.name.endswith(f"___{tool_name}") or tool.name == tool_name
            ),
            None,
        )
        if target_tool is None:
            logger.warning("MCP restaurant tool is unavailable")
            raise RestaurantDataError("mcp_unavailable")

        result = await target_tool.ainvoke(arguments)
        return normalize_restaurant_response(result)
    except RestaurantDataError:
        raise
    except Exception as error:
        logger.error("MCP restaurant request failed (error_type={})", type(error).__name__)
        raise RestaurantDataError("mcp_unavailable") from error


def parse_search_result(
    response: Any,
    query: str,
    search_params: dict[str, Any],
) -> RestaurantSearchResult:
    """Parse normalized Lambda data into a truthful result model."""
    return _parse_search_result(
        response,
        query,
        search_params,
        default_data_source="searchapi",
    )


async def run_restaurant_data_agent(
    query: str,
    cuisine: str | None = None,
    location: str | None = None,
    price_range: str | None = None,
    dietary_restrictions: list[str] | None = None,
    limit: int = 5,
) -> RestaurantSearchResult:
    """Search through SearchAPI and return validated restaurant records."""
    normalized_limit = min(max(1, int(limit)), 10)
    search_params: dict[str, Any] = {
        "query": query,
        "cuisine": cuisine or "",
        "location": location or "",
        "price_range": price_range or "",
        "dietary_restrictions": dietary_restrictions or [],
        "limit": normalized_limit,
    }

    if not is_mcp_configured():
        return RestaurantSearchResult(
            query=query,
            total_results=0,
            restaurants=[],
            search_location=location or None,
            search_filters={},
            data_source="searchapi",
            notes=safe_search_error("missing_mcp_configuration"),
            status="error",
            error_code="missing_mcp_configuration",
        )

    try:
        response = await call_mcp_tool(SEARCH_RESTAURANTS_TOOL, search_params)
        result = parse_search_result(response, query, search_params)
        logger.info(
            "Restaurant search completed (status={}, count={}, source={})",
            result.status,
            result.total_results,
            result.data_source,
        )
        return result
    except RestaurantDataError as error:
        logger.warning("Restaurant data response rejected (error_code={})", error.code)
        return RestaurantSearchResult(
            query=query,
            total_results=0,
            restaurants=[],
            search_location=location or None,
            search_filters={
                key: ", ".join(str(item) for item in value)
                if isinstance(value, list)
                else str(value)
                for key, value in search_params.items()
                if value is not None
            },
            data_source="searchapi",
            notes=safe_search_error(error.code),
            status="error",
            error_code=error.code,
        )
    except Exception as error:
        logger.error("Restaurant data agent failed (error_type={})", type(error).__name__)
        return RestaurantSearchResult(
            query=query,
            total_results=0,
            restaurants=[],
            search_location=location or None,
            search_filters={},
            data_source="searchapi",
            notes=safe_search_error("provider_error"),
            status="error",
            error_code="provider_error",
        )
