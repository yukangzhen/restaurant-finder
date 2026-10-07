"""
API entrypoint for the Restaurant Finder Agent.

Provides the main entrypoint for BedrockAgentCoreApp with lifespan hooks
for initializing infrastructure components.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from loguru import logger

from src.infrastructure.startup import initialize_infrastructure
from src.infrastructure.streaming import stream_response
from src.infrastructure.jev_router import close_jev_router, initialize_jev_router

@asynccontextmanager
async def lifespan(_: BedrockAgentCoreApp) -> AsyncIterator[None]:
    """Initialize infrastructure on startup and close reusable clients on shutdown."""
    logger.info("Application startup initiated")
    results = await initialize_infrastructure()
    jev_ready = await initialize_jev_router()

    # Log initialization summary
    observability_status = results.get("observability", {}).get("status", "unknown")
    guardrail_status = results.get("guardrails", {}).get("status", "unknown")

    logger.info(
        f"Startup complete - Observability: {observability_status}, "
        f"Guardrails: {guardrail_status}, Jev router: {'ready' if jev_ready else 'Bedrock fallback'}"
    )

    if observability_status == "error":
        logger.warning(
            f"Observability initialization error: {results['observability'].get('error')}"
        )

    if guardrail_status == "error":
        logger.warning(
            f"Guardrail initialization error: {results['guardrails'].get('error')}"
        )

    try:
        yield
    finally:
        await close_jev_router()


# Initialize BedrockAgentCoreApp with the lifecycle API supported by the SDK.
app = BedrockAgentCoreApp(lifespan=lifespan)


@app.entrypoint
async def invoke(payload: dict):
    """
    Main entrypoint for the agent.

    Expected payload:
    {
        "prompt": "<user input>",               # Required
        "customer_name": "<customer name>",     # Optional, defaults to "Guest"
        "conversation_id": "<conversation id>", # Optional, unique conversation ID
        "actor_id": "<stable user ID>"           # Optional, stable memory identity
    }

    Returns an async generator for streaming, or dict for errors.
    """
    user_input = payload.get("prompt", "")
    if not user_input:
        return {"error": "No prompt provided in the payload."}

    # Extract optional customer context
    customer_name = payload.get("customer_name", "Guest")
    conversation_id = payload.get("conversation_id")
    actor_id = payload.get("actor_id")

    # Return async generator - BedrockAgentCoreApp handles streaming automatically
    return stream_response(
        user_input=user_input,
        customer_name=customer_name,
        conversation_id=conversation_id,
        actor_id=actor_id,
    )


if __name__ == "__main__":
    app.run()
