"""Run one complete orchestrator turn and return its final approved response."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger

from src.application.orchestrator.identity import resolve_request_identity
from src.application.orchestrator.workflow.graph import create_orchestrator_graph
from src.infrastructure.model import extract_text_content


@dataclass(frozen=True)
class TurnResult:
    """Complete final response returned only after output guardrail processing."""

    text: str
    blocked: bool = False


async def run_orchestrator_turn(
    messages: str | list[str] | list[dict[str, Any]],
    customer_name: str = "Guest",
    conversation_id: str | None = None,
    actor_id: str | None = None,
) -> TurnResult:
    """Execute the graph exactly once for a user turn and return safe final text."""
    identity = resolve_request_identity(conversation_id, actor_id)
    config = {
        "configurable": {
            "thread_id": identity.conversation_id,
            "customer_name": customer_name,
            "actor_id": identity.actor_id,
        }
    }
    input_data = {
        "messages": _format_messages(messages),
        "customer_name": customer_name,
        # These fields are overwritten on every graph invocation, even when
        # LangGraph restores the rest of the conversation from its checkpointer.
        "tool_call_count": 0,
        "made_tool_calls": False,
        "response_status": "pending",
        "rag_status": None,
        "rag_generation": None,
        "rag_pending_scope": None,
        "rag_retrieval_count": 0,
    }

    logger.info("Starting one workflow turn (conversation_id={})", identity.conversation_id)
    result = await create_orchestrator_graph().ainvoke(input=input_data, config=config)
    response_text = _extract_final_response(result)
    if not response_text:
        raise RuntimeError("The workflow did not produce a final response")

    return TurnResult(
        text=response_text,
        blocked=result.get("response_status") == "blocked",
    )


def _extract_final_response(state: dict) -> str:
    """Extract this turn's final AI message, excluding earlier conversation text."""
    messages = state.get("messages", [])
    latest_user_index = next(
        (
            index
            for index in range(len(messages) - 1, -1, -1)
            if isinstance(messages[index], HumanMessage)
        ),
        -1,
    )
    for message in reversed(messages[latest_user_index + 1 :]):
        if isinstance(message, AIMessage) and not message.tool_calls:
            content = extract_text_content(message.content)
            if content:
                return re.sub(r"<thinking>.*?</thinking>\s*", "", content, flags=re.DOTALL).strip()
    return ""


def _format_messages(
    messages: str | list[str] | list[dict[str, Any]],
) -> list[HumanMessage | AIMessage]:
    """Convert a prompt or role/content history into LangChain message objects."""
    if isinstance(messages, str):
        return [_new_human_message(messages)]

    if not isinstance(messages, list) or not messages:
        return []

    if isinstance(messages[0], dict) and "role" in messages[0]:
        formatted = []
        for message in messages:
            content = message.get("content", "")
            if message.get("role") == "user":
                formatted.append(_new_human_message(content))
            elif message.get("role") == "assistant":
                formatted.append(AIMessage(content=content, id=str(uuid.uuid4())))
        return formatted

    return [_new_human_message(str(message)) for message in messages]


def _new_human_message(content: str) -> HumanMessage:
    """Assign turn metadata before LangGraph checkpoints this request."""
    return HumanMessage(
        content=content,
        id=str(uuid.uuid4()),
        additional_kwargs={
            "agentcore_event_timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
