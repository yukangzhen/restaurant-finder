"""TypeSafe Jev intent classification with a reusable async client."""

import asyncio
from dataclasses import dataclass

import boto3
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from loguru import logger
from pydantic import SecretStr
from typesafe_sdk import AsyncTypeSafeClient, Choice, RetryPolicy

from src.config import settings
from src.infrastructure.model import extract_text_content


@dataclass(frozen=True)
class JevClassification:
    """Typed routing answer returned by Jev."""

    intent: str
    confidence: float | None


class JevRouterUnavailable(RuntimeError):
    """Raised when Jev cannot provide a valid routing answer."""


_VALID_INTENTS: set[str] = {"restaurant_search", "document_qa", "simple", "off_topic"}
_jev_client: AsyncTypeSafeClient | None = None


async def _load_api_key() -> SecretStr | None:
    """Load the router key from local settings or its deployed secret."""
    if settings.TYPESAFE_API_KEY is not None:
        return settings.TYPESAFE_API_KEY

    if not settings.TYPESAFE_SECRET_ARN:
        return None

    def read_secret() -> str:
        response = boto3.client(
            "secretsmanager",
            region_name=settings.AWS_REGION,
        ).get_secret_value(SecretId=settings.TYPESAFE_SECRET_ARN)
        return response.get("SecretString", "")

    try:
        secret_value = await asyncio.to_thread(read_secret)
        return SecretStr(secret_value) if secret_value else None
    except Exception as error:
        logger.warning(
            "Could not load TypeSafe key from Secrets Manager; Bedrock fallback will be used (error_type={})",
            type(error).__name__,
        )
        return None


def _message_for_jev(message: BaseMessage) -> dict:
    """Convert a LangChain message into a compact, role-labelled record."""
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"
    elif isinstance(message, ToolMessage):
        role = "tool"
    else:
        role = message.type

    content = extract_text_content(message.content)
    if message.additional_kwargs.get("document_rag_response"):
        content = "Previous document response; restaurant scope is supplied in trusted routing context."
    item = {"role": role, "content": content}

    if isinstance(message, AIMessage) and message.tool_calls:
        item["tool_calls"] = [
            {"name": call.get("name"), "args": call.get("args")}
            for call in message.tool_calls
        ]
    elif isinstance(message, ToolMessage):
        item["tool_name"] = message.name
        item["tool_call_id"] = message.tool_call_id

    return item


def bedrock_routing_messages(messages):
    """Classification needs conversational text, without tool payloads or corpus passages."""
    output = []
    for message in messages[-8:]:
        if not isinstance(message,(HumanMessage,AIMessage)) or getattr(message,"tool_calls",None):
            continue
        content = _message_for_jev(message)["content"]
        output.append(type(message)(content=content[:2000]))
    return output


async def initialize_jev_router() -> bool:
    """Open the reusable Jev client; leave it unavailable if setup fails."""
    global _jev_client

    if _jev_client is not None:
        return True

    api_key = await _load_api_key()
    if api_key is None:
        logger.warning("TYPESAFE_API_KEY is not configured; router requests will use Bedrock fallback")
        return False

    client = None
    try:
        client = AsyncTypeSafeClient(
            api_key=api_key.get_secret_value(),
            model=settings.JEV_ROUTER_MODEL,
            retry=RetryPolicy(
                max_retries=0,
                timeout=settings.JEV_ROUTER_TIMEOUT_SECONDS,
            ),
        )
        await client.__aenter__()
        _jev_client = client
        logger.info("Jev router initialized (model={})", settings.JEV_ROUTER_MODEL)
        return True
    except Exception as error:
        if client is not None:
            try:
                await client.__aexit__(type(error), error, error.__traceback__)
            except Exception:
                pass
        logger.warning(
            "Could not initialize Jev router; Bedrock fallback will be used (error_type={})",
            type(error).__name__,
        )
        return False


async def close_jev_router() -> None:
    """Close the reusable Jev HTTP client during application shutdown."""
    global _jev_client

    client, _jev_client = _jev_client, None
    if client is None:
        return

    try:
        await client.__aexit__(None, None, None)
    except Exception as error:
        logger.warning("Could not close Jev router client (error_type={})", type(error).__name__)


async def classify_with_jev(messages: list[BaseMessage], approved_document_scope: str | None = None) -> JevClassification:
    """Classify the latest user message while preserving the conversation context."""
    if _jev_client is None:
        raise JevRouterUnavailable("Jev router client is not initialized")

    from src.application.document_rag.retrieval import router_catalog
    response = await _jev_client.system_one(
        state={"messages": [_message_for_jev(message) for message in messages[-8:]],
               "fictional_document_catalog": router_catalog(), "approved_document_scope": approved_document_scope},
        questions={
            "intent": Choice(
                instructions=(
                    "Classify only the latest user message. Use earlier messages only to resolve "
                    "references or follow-ups. Choose document_qa for questions about controlled "
                    "menus, policies or uploaded documents; questions about the fictional catalog; "
                    "and document follow-ups when approved_document_scope is present. Missing "
                    "scope is clarified by document_qa. This takes priority over restaurant_search. "
                    "Greetings/thanks remain simple. Choose restaurant_search both when the user wants "
                    "actual restaurant results, recommendations, or details and when they ask "
                    "to recall dining preferences, past restaurant recommendations, or dining "
                    "facts from memory. In this restaurant-finder conversation, an unqualified "
                    "question such as 'What preferences have I told you before?' means dining "
                    "preferences and is a memory request. A memory request does not require a "
                    "location or a request for new restaurant results. A greeting, thanks, "
                    "acknowledgment, goodbye, or "
                    "question about the assistant's capabilities is simple, even if it mentions "
                    "restaurants, food, or cuisine. Choose off_topic for unrelated requests."
                ),
                criteria={
                    "document_qa": (
                        "The user asks what controlled/uploaded documents, menus or policies say; "
                        "asks specific menu/price/policy details for Harbor Pasta Lab, Sakura Table Lab "
                        "or Spice Garden Lab; or follows up on an approved document answer. "
                        "Document questions lacking a restaurant still use this route for clarification."
                    ),
                    "restaurant_search": (
                        "The user wants actual restaurant results, recommendations, or details "
                        "about a specific restaurant, meal, cuisine, or dietary option; OR wants "
                        "to recall their own dining preferences, restaurant recommendations, or "
                        "dining facts from earlier conversations. Memory recall is in scope even "
                        "without a location or a request for new restaurant results. In this "
                        "restaurant-finder conversation, an unqualified question such as 'What "
                        "preferences have I told you before?' means dining preferences. This also "
                        "includes follow-up questions about a restaurant already discussed."
                    ),
                    "simple": (
                        "A greeting, thanks, acknowledgment, goodbye, or a question about the "
                        "assistant and its capabilities, such as 'What kinds of restaurants can "
                        "you help me find?' This remains simple even when it mentions restaurants "
                        "or food."
                    ),
                    "off_topic": (
                        "A request unrelated to restaurants, food, dining, or the assistant's "
                        "capabilities, such as weather, coding, math, jokes, or sports."
                    ),
                },
            )
        },
    )

    answer = response.choices.get("intent")
    intent = answer.choice if answer is not None else None
    if intent not in _VALID_INTENTS:
        raise JevRouterUnavailable("Jev returned an invalid intent")

    confidence = answer.confidence
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        confidence = None

    return JevClassification(intent=intent, confidence=confidence)
