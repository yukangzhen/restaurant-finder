"""Shared parsing and validation for restaurant search provider responses."""

from __future__ import annotations

import json
import re
from typing import Any

from src.domain.models import PRICE_RANGE_MAP, Restaurant, RestaurantSearchResult


class RestaurantDataError(ValueError):
    """Provider response failure with a safe, stable error code."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


_ERROR_MESSAGES = {
    "provider_http_error": "The restaurant search provider returned an error.",
    "provider_error": "The restaurant search provider could not complete the request.",
    "invalid_response": "The restaurant search provider returned an invalid response.",
    "mcp_unavailable": "The restaurant search service is temporarily unavailable.",
    "missing_mcp_configuration": "The restaurant search service is not configured.",
}


def safe_search_error(code: str) -> str:
    """Return a user-safe message for a sanitized provider error code."""
    return _ERROR_MESSAGES.get(code, "The restaurant search could not be completed.")


def _decode_json(value: str) -> Any:
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError) as error:
        raise RestaurantDataError("invalid_response") from error


def normalize_restaurant_response(raw: Any, max_envelopes: int = 4) -> dict[str, Any]:
    """Normalize MCP content, JSON text, and nested Lambda response envelopes."""
    current = raw
    unwrapped = 0
    while True:
        if isinstance(current, list):
            if current and all(
                isinstance(block, dict) and block.get("type") == "text"
                for block in current
            ):
                current = "\n".join(str(block.get("text", "")) for block in current)
                continue
            raise RestaurantDataError("invalid_response")

        if isinstance(current, str):
            current = _decode_json(current)
            continue

        if not isinstance(current, dict):
            raise RestaurantDataError("invalid_response")

        status_code = current.get("statusCode")
        if status_code is not None:
            try:
                status_code = int(status_code)
            except (TypeError, ValueError) as error:
                raise RestaurantDataError("invalid_response") from error
            if status_code < 200 or status_code >= 300:
                raise RestaurantDataError("provider_http_error")

        if "body" in current:
            if unwrapped >= max_envelopes:
                raise RestaurantDataError("invalid_response")
            current = current["body"]
            unwrapped += 1
            continue

        if "result" in current and isinstance(current["result"], (dict, str, list)):
            if unwrapped >= max_envelopes:
                raise RestaurantDataError("invalid_response")
            current = current["result"]
            unwrapped += 1
            continue

        return current


def _optional_text(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _rating(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if 0 <= parsed <= 5 else None


def _review_count(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        return int(value) if value >= 0 and value.is_integer() else None
    if isinstance(value, str):
        match = re.fullmatch(
            r"\s*([0-9][0-9,]*)\+?(?:\s+reviews?)?\s*", value, re.IGNORECASE
        )
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                return None
    return None


def _optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def parse_restaurant(data: Any) -> Restaurant:
    """Build a restaurant only from a record with a source-provided name."""
    if not isinstance(data, dict):
        raise RestaurantDataError("invalid_response")

    name = _optional_text(data.get("name"))
    if not name:
        raise RestaurantDataError("invalid_response")

    raw_price = data.get("price_range")
    if raw_price is None:
        raw_price = data.get("price")
    price_text = _optional_text(raw_price)
    price_range = PRICE_RANGE_MAP.get(price_text) if price_text else None
    price_description = _optional_text(data.get("price_description"))
    if price_description is None and price_text and price_range is None:
        price_description = price_text

    return Restaurant(
        name=name,
        cuisine_type=_optional_text(data.get("cuisine_type")),
        rating=_rating(data.get("rating")),
        review_count=_review_count(data.get("review_count")),
        price_range=price_range,
        price_description=price_description,
        address=_optional_text(data.get("address")),
        city=_optional_text(data.get("city")),
        phone=_optional_text(data.get("phone")),
        website=_optional_text(data.get("website")),
        features=_string_list(data.get("features")),
        dietary_options=_string_list(data.get("dietary_options")),
        operating_hours=_optional_text(data.get("operating_hours")),
        distance=_optional_text(data.get("distance")),
        reservation_available=_optional_bool(data.get("reservation_available")),
    )


def parse_search_result(
    raw_response: Any,
    query: str,
    search_params: dict[str, Any] | None = None,
    *,
    default_data_source: str = "unknown",
) -> RestaurantSearchResult:
    """Normalize a provider response and build a truthful result model."""
    payload = normalize_restaurant_response(raw_response)
    params = search_params or {}
    raw_restaurants = payload.get("restaurants", [])
    if not isinstance(raw_restaurants, list):
        raise RestaurantDataError("invalid_response")

    restaurants: list[Restaurant] = []
    for record in raw_restaurants:
        try:
            restaurants.append(parse_restaurant(record))
        except RestaurantDataError:
            continue

    web_sources: list[dict[str, str]] = []
    raw_sources = payload.get("web_sources", payload.get("sources", []))
    if isinstance(raw_sources, list):
        for source in raw_sources:
            if not isinstance(source, dict):
                continue
            normalized_source = {
                key: value.strip()
                for key in ("title", "url", "snippet")
                if isinstance((value := source.get(key)), str) and value.strip()
            }
            if normalized_source:
                web_sources.append(normalized_source)

    raw_error = payload.get("error")
    error_code_candidate = _optional_text(payload.get("error_code"))
    error_code = (
        error_code_candidate
        if error_code_candidate and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", error_code_candidate)
        else ("provider_error" if error_code_candidate else None)
    )
    status = payload.get("status")
    if status not in {"success", "empty", "error"}:
        status = "error" if raw_error or error_code else ("success" if restaurants else "empty")
    elif status == "success" and not restaurants:
        status = "empty"
    elif status == "empty" and restaurants:
        status = "success"
    if status == "error" and not error_code:
        error_code = "provider_error"

    message = _optional_text(payload.get("message"))
    if status == "error":
        message = safe_search_error(error_code or "provider_error")

    filters = {
        key: ", ".join(str(item) for item in value) if isinstance(value, list) else str(value)
        for key, value in params.items()
        if value is not None
    }

    return RestaurantSearchResult(
        query=query,
        total_results=len(restaurants),
        restaurants=restaurants,
        search_location=_optional_text(params.get("location")),
        search_filters=filters,
        data_source=_optional_text(payload.get("data_source")) or default_data_source,
        notes=message,
        status=status,
        error_code=error_code if status == "error" else None,
        web_sources=web_sources,
    )
