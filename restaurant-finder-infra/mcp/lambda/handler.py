import json
import os
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

SEARCH_BASE_URL = "https://www.searchapi.io/api/v1/search"
_cached_api_key: str | None = None


def _get_search_api_key() -> str:
    """
    Retrieve the search API key from AWS Secrets Manager.

    Cached after first retrieval to avoid repeated calls during warm starts.
    """
    global _cached_api_key

    if _cached_api_key is not None:
        return _cached_api_key

    secret_name = os.environ.get("SEARCH_SECRET_NAME")

    if not secret_name:
        raise RuntimeError(
            "SEARCH_SECRET_NAME environment variable not set. "
            "Configure the secret in AWS Secrets Manager."
        )

    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)

        secret_string = response["SecretString"]

        try:
            secret_data = json.loads(secret_string)
            if isinstance(secret_data, dict):
                _cached_api_key = (
                    secret_data.get("api_key")
                    or secret_data.get("key")
                    or secret_string
                )
            else:
                _cached_api_key = secret_string
        except json.JSONDecodeError:
            # Plain text secret
            _cached_api_key = secret_string

        return _cached_api_key

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        raise RuntimeError(
            f"Failed to retrieve secret from Secrets Manager: {error_code}. "
            f"Ensure '{secret_name}' exists and Lambda has read access."
        )


def lambda_handler(event, context):
    """Route tool invocations from the AgentCore Gateway."""
    try:
        extended_name = context.client_context.custom.get("bedrockAgentCoreToolName")
        tool_name = None

        if extended_name and "___" in extended_name:
            tool_name = extended_name.split("___", 1)[1]

        if not tool_name:
            return _response(400, {"error": "Missing tool name"})

        if tool_name == "search_restaurants":
            result = search_restaurants(event)
            return _response(200, {"result": result})
        else:
            return _response(400, {"error": f"Unknown tool '{tool_name}'"})

    except Exception:
        return _response(500, {"error": "Restaurant search failed", "error_code": "SEARCH_PROVIDER_ERROR"})


def _response(status_code: int, body: Dict[str, Any]):
    return {"statusCode": status_code, "body": json.dumps(body)}


def _search_local(query: str, location: str = "", num_results: int = 10) -> Dict[str, Any]:
    """Search using google_local engine for structured local business data."""
    api_key = _get_search_api_key()

    params = {
        "api_key": api_key,
        "engine": "google_local",
        "q": query,
        "num": str(num_results),
    }

    if location and location.strip():
        params["location"] = location.strip()

    url = f"{SEARCH_BASE_URL}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Search HTTP error {e.code}") from e
    except urllib.error.URLError as e:
        raise RuntimeError("Search connection failed") from e


def _search_web(query: str, num_results: int = 10) -> Dict[str, Any]:
    """Fallback web search using google engine."""
    api_key = _get_search_api_key()

    params = {
        "api_key": api_key,
        "engine": "google",
        "q": query,
        "num": str(num_results),
    }

    url = f"{SEARCH_BASE_URL}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Search HTTP error {e.code}") from e
    except urllib.error.URLError as e:
        raise RuntimeError("Search connection failed") from e


def _build_search_query(
    query: str = "",
    cuisine: str = "",
    location: str = "",
    price_range: str = "",
    dietary_restrictions: List[str] = None,
) -> str:
    """Build a composite search query from structured parameters."""
    parts = []

    if query and query.strip():
        parts.append(query.strip())

    if cuisine and cuisine.strip():
        parts.append(f"{cuisine.strip()} restaurants")
    elif not query:
        parts.append("restaurants")

    if location and location.strip():
        parts.append(f"in {location.strip()}")

    price_descriptions = {
        "$": "budget-friendly cheap",
        "$$": "moderate mid-range",
        "$$$": "upscale high-end",
        "$$$$": "fine dining luxury",
    }
    if price_range and price_range in price_descriptions:
        parts.append(price_descriptions[price_range])

    if dietary_restrictions:
        if isinstance(dietary_restrictions, str):
            dietary_restrictions = [d.strip() for d in dietary_restrictions.split(",") if d.strip()]
        if dietary_restrictions:
            parts.append(" ".join(dietary_restrictions))

    return " ".join(parts)


def _parse_local_results(
    api_response: Dict[str, Any],
    location: str,
    cuisine: str,
    price_range: str,
    limit: int,
) -> List[Dict[str, Any]]:
    """Parse google_local response into structured restaurant objects."""
    restaurants = []
    local_results = api_response.get("local_results", [])

    for result in local_results[:limit]:
        if not isinstance(result, dict):
            continue
        name = result.get("title") or result.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        rating = result.get("rating")
        if isinstance(rating, bool):
            rating = None
        try:
            rating = float(rating) if rating is not None else None
            if rating is not None and not 0 <= rating <= 5:
                rating = None
        except (TypeError, ValueError):
            rating = None

        reviews = result.get("reviews", result.get("review_count"))
        try:
            reviews = int(reviews) if reviews is not None else None
            if reviews is not None and reviews < 0:
                reviews = None
        except (TypeError, ValueError):
            reviews = None

        type_info = result.get("type", result.get("types", ""))
        if isinstance(type_info, list):
            cuisine_type = ", ".join(item for item in type_info[:3] if isinstance(item, str)) or None
        else:
            cuisine_type = type_info if isinstance(type_info, str) and type_info else None

        address = result.get("address", "")
        service_options = result.get("service_options", {})
        features = []
        if isinstance(service_options, dict):
            if service_options.get("dine_in"):
                features.append("Dine-in")
            if service_options.get("takeout"):
                features.append("Takeout")
            if service_options.get("delivery"):
                features.append("Delivery")
        elif isinstance(service_options, list):
            features = service_options

        hours = result.get("hours", result.get("operating_hours", ""))
        if isinstance(hours, dict):
            hours = hours.get("today", "")

        raw_price = result.get("price")
        known_price_categories = {"$", "$$", "$$$", "$$$$"}
        price_range_value = raw_price if isinstance(raw_price, str) and raw_price in known_price_categories else None
        price_description = raw_price if isinstance(raw_price, str) and raw_price not in known_price_categories else None
        restaurant = {
            "name": name,
            "cuisine_type": cuisine_type,
            "rating": round(rating, 1) if rating is not None else None,
            "review_count": reviews,
            "price_range": price_range_value,
            "price_description": price_description,
            "address": address[:200] if address else "",
            "city": result.get("city"),
            "neighborhood": result.get("neighborhood", ""),
            "features": features,
            "dietary_options": [],
            "operating_hours": hours if isinstance(hours, str) else "",
            "reservation_available": result.get("reservation_available"),
            "phone": result.get("phone", ""),
            "website": result.get("website", result.get("link", "")),
            "thumbnail": result.get("thumbnail", ""),
            "gps_coordinates": result.get("gps_coordinates", {}),
            "place_id": result.get("place_id", ""),
            "source": "google_local",
        }
        restaurants.append(restaurant)

    return restaurants


def _parse_web_results(
    api_response: Dict[str, Any],
    location: str,
    cuisine: str,
    price_range: str,
    limit: int,
) -> List[Dict[str, Any]]:
    """Preserve generic organic pages as sources, never as restaurant records."""
    sources = []
    organic_results = api_response.get("organic_results", [])

    for result in organic_results[:limit]:
        if not isinstance(result, dict):
            continue
        source = {
            key: result[key]
            for key in ("title", "link", "snippet")
            if isinstance(result.get(key), str) and result[key].strip()
        }
        if source:
            if "link" in source:
                source["url"] = source.pop("link")
            sources.append(source)
    return sources


def search_restaurants(event: Dict[str, Any]) -> Dict[str, Any]:
    """Search for restaurants. Tries local search first, falls back to web."""
    query = event.get("query", "").strip()
    cuisine = event.get("cuisine", "").strip()
    location = event.get("location", "").strip()
    price_range = event.get("price_range", "")
    dietary_restrictions = event.get("dietary_restrictions", [])
    limit = min(max(1, int(event.get("limit", 5))), 10)

    if isinstance(dietary_restrictions, str):
        dietary_restrictions = [d.strip() for d in dietary_restrictions.split(",") if d.strip()]

    search_query = _build_search_query(
        query=query,
        cuisine=cuisine,
        location=location,
        price_range=price_range,
        dietary_restrictions=dietary_restrictions,
    )

    restaurants = []
    web_sources = []
    data_source = "google_local"
    provider_failed = False

    try:
        api_response = _search_local(
            query=search_query,
            location=location,
            num_results=limit * 2,
        )

        restaurants = _parse_local_results(
            api_response=api_response,
            location=location,
            cuisine=cuisine,
            price_range=price_range,
            limit=limit,
        )

        if not restaurants:
            data_source = "web_search"
            api_response = _search_web(search_query, num_results=limit * 2)
            web_sources = _parse_web_results(
                api_response=api_response, location=location, cuisine=cuisine,
                price_range=price_range, limit=limit,
            )

    except Exception:
        provider_failed = True
        try:
            data_source = "web_search"
            api_response = _search_web(search_query, num_results=limit * 2)
            web_sources = _parse_web_results(
                api_response=api_response, location=location, cuisine=cuisine,
                price_range=price_range, limit=limit,
            )
            provider_failed = False
        except Exception:
            provider_failed = True

    restaurants.sort(
        key=lambda item: item["rating"] if isinstance(item.get("rating"), (int, float)) else -1,
        reverse=True,
    )

    result = {
        "restaurants": restaurants,
        "total_found": len(restaurants),
        "search_params": {
            "query": query,
            "cuisine": cuisine or "any",
            "location": location or "any",
            "price_range": price_range,
            "dietary_restrictions": dietary_restrictions,
            "limit": limit,
        },
        "search_query_used": search_query,
        "data_source": data_source,
        "message": (
            f"Found {len(restaurants)} restaurants via {data_source}."
            if restaurants else "No verified restaurant records were returned."
        ),
        "status": "error" if provider_failed else ("success" if restaurants else "empty"),
        "error_code": "SEARCH_PROVIDER_UNAVAILABLE" if provider_failed else None,
        "web_sources": web_sources,
    }

    return result

