"""SSE API boundary with input and output moderation enforcement."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from loguru import logger

from src.application.orchestrator.identity import resolve_request_identity
from src.application.orchestrator.streaming import run_orchestrator_turn
from src.infrastructure.guardrails import (
    GuardrailUnavailableError,
    apply_input_guardrail,
    get_blocked_input_message,
)
from src.infrastructure.observability import get_observability_manager


def _event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def stream_response(
    user_input: str,
    customer_name: str = "Guest",
    conversation_id: str | None = None,
    actor_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """Run one buffered turn and emit only the complete, approved answer."""
    try:
        identity = resolve_request_identity(conversation_id, actor_id)
    except ValueError:
        yield _event({"error": "The conversation identity is invalid."})
        yield _event({"done": True})
        return

    observability = get_observability_manager()
    with observability.session_context(identity.conversation_id):
        observability.add_span_event(
            "request.start",
            attributes={
                "session.id": identity.conversation_id,
                "input.length": len(user_input),
            },
        )
        try:
            with observability.create_span(
                "guardrail.input",
                attributes={"input.length": len(user_input)},
            ):
                input_result = await asyncio.to_thread(apply_input_guardrail, user_input)

            if not input_result.allowed:
                yield _event({"blocked": True, "message": get_blocked_input_message()})
                yield _event({"done": True})
                return

            with observability.create_span(
                "workflow.execution",
                attributes={"session.id": identity.conversation_id},
            ):
                turn = await run_orchestrator_turn(
                    messages=input_result.output,
                    customer_name=customer_name,
                    conversation_id=identity.conversation_id,
                    actor_id=identity.actor_id,
                )

            if turn.blocked:
                yield _event({"blocked": True, "message": turn.text})
            elif turn.text:
                # A single complete chunk preserves the SSE contract while
                # ensuring no unchecked token reaches the client.
                payload = {"chunk": turn.text}
                if turn.citations:
                    payload["citations"] = [c.model_dump() for c in turn.citations]
                yield _event(payload)

            observability.add_span_event(
                "request.complete",
                attributes={
                    "session.id": identity.conversation_id,
                    "output.length": len(turn.text),
                    "blocked": turn.blocked,
                },
            )
            yield _event({"done": True})
        except GuardrailUnavailableError:
            logger.error("Request stopped because an enabled guardrail was unavailable")
            observability.add_span_event(
                "request.error",
                attributes={"error.type": "GuardrailUnavailableError"},
            )
            yield _event(
                {
                    "error": (
                        "The safety check is temporarily unavailable, so I couldn't "
                        "process this request. Please try again later."
                    )
                }
            )
            yield _event({"done": True})
        except Exception as error:
            error_type = type(error).__name__
            logger.error("Request failed (error_type={})", error_type)
            observability.add_span_event(
                "request.error",
                attributes={"error.type": error_type},
            )
            yield _event(
                {"error": "The request could not be completed. Please try again later."}
            )
            yield _event({"done": True})
