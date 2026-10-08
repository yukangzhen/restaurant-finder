import asyncio
from datetime import datetime, timezone
import hashlib
import time
import uuid
from typing import cast
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from loguru import logger

from src.application.orchestrator.workflow.state import OrchestratorState, IntentType
from src.application.orchestrator.workflow.edges import MAX_TOOL_CALLS_PER_TURN
from src.application.orchestrator.workflow.chains import (
    get_search_agent_chain,
    get_router_chain,
    get_simple_response_chain,
)
from src.config import settings
from src.infrastructure.model import extract_text_content as _extract_text_content
from src.infrastructure.memory import get_memory_instance
from src.infrastructure.observability import get_observability_manager
from src.infrastructure.jev_router import classify_with_jev
from src.infrastructure.guardrails import (
    apply_output_guardrail,
    get_blocked_output_message,
)


async def search_agent_node(
    state: OrchestratorState,
    config: RunnableConfig,
) -> dict:
    """
    Search agent node implementing the ReAct (Reasoning + Acting) pattern.

    This node handles restaurant search requests using the search agent chain
    which has tools bound for finding and researching restaurants.

    ReAct Pattern:
    1. Thought: Agent reasons about what to do next
    2. Action: Agent calls a tool OR provides Final Answer
    3. Observation: Tool results are returned (handled by ToolNode)
    4. Loop back to step 1 until Final Answer

    The LLM decides which tools to call based on the user's request:
    - memory_retrieval_tool: For fetching user preferences/facts/summaries
    - restaurant_data_tool: For MCP Gateway searches
    - restaurant_explorer_tool: For web-based searches
    - restaurant_research_tool: For detailed restaurant research

    Args:
        state: The orchestrator state containing messages.
        config: Runtime configuration with customer context.

    Returns:
        Updated state with the search agent's response.
    """
    observability = get_observability_manager()
    start_time = time.time()

    configurable = config.get("configurable", {})
    customer_name = configurable.get("customer_name", "Guest")
    tool_call_count = state.get("tool_call_count", 0)
    react_iteration = tool_call_count + 1  # Track which ReAct loop iteration
    remaining_tool_calls = max(0, MAX_TOOL_CALLS_PER_TURN - tool_call_count)

    messages = list(state["messages"])

    # Get the chain and prompt metadata for tracing
    chain_result = get_search_agent_chain(
        customer_name=customer_name,
        allow_tool_calls=remaining_tool_calls > 0,
    )
    prompt_meta = chain_result.prompt_metadata

    logger.debug(
        f"Search agent invoked: iteration={react_iteration}, "
        f"messages={len(messages)}, prompt_version={prompt_meta.version}"
    )

    # Build comprehensive span attributes for observability
    span_attributes = {
        # Prompt metadata (for prompt version tracking)
        "prompt.name": prompt_meta.name,
        "prompt.version": prompt_meta.version or "unknown",
        "prompt.id": prompt_meta.id or "unknown",
        # ReAct loop state
        "react.iteration": react_iteration,
        "react.tool_call_count": tool_call_count,
        # Request context
        "message.count": len(messages),
        "input.token_estimate": sum(
            len(str(m.content)) // 4 for m in messages if hasattr(m, "content")
        ),
    }

    with observability.create_span(
        "search_agent.invoke",
        attributes=span_attributes,
    ):
        response = await chain_result.chain.ainvoke(
            {"messages": messages},
            config,
        )

    # Track tool calls for efficiency limiting
    requested_tool_calls = getattr(response, "tool_calls", []) or []
    if len(requested_tool_calls) > remaining_tool_calls:
        # Keep only executable calls in the message. Dropped calls never enter
        # graph state, so there can be no unmatched tool-call IDs.
        response = response.model_copy(
            update={"tool_calls": requested_tool_calls[:remaining_tool_calls]}
        )
    tool_calls = getattr(response, "tool_calls", []) or []
    has_tool_calls = bool(tool_calls)
    new_tool_count = tool_call_count + len(tool_calls)
    tool_names = [tc.get("name", "unknown") for tc in tool_calls]

    # Record workflow step completion with comprehensive metadata
    duration_ms = (time.time() - start_time) * 1000
    observability.record_workflow_step(
        step_name="search_agent",
        step_type="node",
        duration_ms=duration_ms,
        success=True,
        metadata={
            # Prompt tracking
            "prompt.name": prompt_meta.name,
            "prompt.version": prompt_meta.version or "unknown",
            # ReAct state
            "react.iteration": str(react_iteration),
            "react.has_tool_calls": str(has_tool_calls),
            "react.tool_names": ",".join(tool_names) if tool_names else "none",
            # Response metrics
            "response.has_content": str(bool(response.content)),
            "output.token_estimate": str(len(str(response.content)) // 4) if response.content else "0",
        }
    )

    if has_tool_calls:
        logger.debug(f"Search agent requested tools: {tool_names}")
    else:
        logger.debug("Search agent provided Final Answer (no tool calls)")

    return {
        "messages": response,
        "tool_call_count": new_tool_count,
        "made_tool_calls": state.get("made_tool_calls", False) or has_tool_calls,
    }


async def output_guardrail_node(
    state: OrchestratorState,
    config: RunnableConfig,
) -> dict:
    """Approve, anonymize, or replace the complete answer before persistence."""
    messages = state.get("messages", [])
    latest_user_index = next(
        (
            index
            for index in range(len(messages) - 1, -1, -1)
            if isinstance(messages[index], HumanMessage)
        ),
        -1,
    )
    final_message = next(
        (
            message
            for message in reversed(messages[latest_user_index + 1 :])
            if isinstance(message, AIMessage) and not message.tool_calls
        ),
        None,
    )
    raw_text = _extract_text_content(final_message.content) if final_message else ""
    if not raw_text.strip():
        raw_text = "I couldn't prepare a complete answer. Please try again."

    observability = get_observability_manager()
    with observability.create_span(
        "guardrail.output",
        attributes={"output.length": len(raw_text)},
    ):
        result = await asyncio.to_thread(apply_output_guardrail, raw_text)

    if result.allowed:
        approved_text = result.output
        response_status = "approved"
        if approved_text != raw_text:
            observability.add_span_event(
                "guardrail.anonymized",
                attributes={"action": result.action},
            )
    else:
        approved_text = get_blocked_output_message()
        response_status = "blocked"
        observability.add_span_event(
            "guardrail.blocked",
            attributes={"action": result.action},
        )

    replacement = AIMessage(
        content=approved_text,
        id=(final_message.id if final_message and final_message.id else str(uuid.uuid4())),
    )
    return {"messages": replacement, "response_status": response_status}


async def router_node(
    state: OrchestratorState,
    config: RunnableConfig,
) -> dict:
    """
    Router node that classifies user intent for routing decisions.

    Intent types:
    - restaurant_search: Route to the search agent with tools
    - simple: Route to simple response (no tools needed)
    - off_topic: Route to simple response with redirect

    Args:
        state: The orchestrator state containing messages.
        config: Runtime configuration.

    Returns:
        Updated state with the classified intent.
    """
    observability = get_observability_manager()
    start_time = time.time()

    messages = list(state["messages"])

    with observability.create_span(
        "router.classify",
        attributes={"message.count": len(messages)},
    ) as router_span:
        provider = "jev"
        model = settings.JEV_ROUTER_MODEL
        confidence = None
        fallback_reason = None

        try:
            with observability.create_span(
                "router.jev",
                attributes={"router.model": model},
            ):
                classification = await classify_with_jev(messages)
            intent = cast(IntentType, classification.intent)
            confidence = classification.confidence
        except Exception as error:
            provider = "bedrock"
            model = settings.ROUTER_MODEL_ID
            fallback_reason = type(error).__name__
            logger.warning(
                "Jev routing failed; using Bedrock fallback (error_type={})",
                fallback_reason,
            )

            with observability.create_span(
                "router.bedrock_fallback",
                attributes={
                    "router.model": model,
                    "fallback.reason": fallback_reason,
                },
            ):
                response = await get_router_chain().ainvoke(
                    {"messages": messages},
                    config,
                )

            response_text = _extract_text_content(response.content).strip().lower()
            if "restaurant_search" in response_text:
                intent = "restaurant_search"
            elif "simple" in response_text:
                intent = "simple"
            elif "off_topic" in response_text:
                intent = "off_topic"
            else:
                logger.warning("Unclear Bedrock fallback intent; defaulting to restaurant_search")
                intent = "restaurant_search"

        if router_span is not None:
            router_span.set_attribute("router.intent", intent)
            router_span.set_attribute("router.provider", provider)
            router_span.set_attribute("router.model", model)
            if confidence is not None:
                router_span.set_attribute("router.confidence", confidence)
            if fallback_reason is not None:
                router_span.set_attribute("router.fallback.reason", fallback_reason)

    duration_ms = (time.time() - start_time) * 1000
    observability.record_workflow_step(
        step_name="router",
        step_type="node",
        duration_ms=duration_ms,
        success=True,
        metadata={
            "intent": intent,
            "provider": provider,
            "model": model,
            "confidence": confidence,
            "fallback_reason": fallback_reason,
        },
    )

    logger.info(
        "Router classified intent={} provider={} model={} fallback_reason={}",
        intent,
        provider,
        model,
        fallback_reason or "none",
    )

    return {"intent": intent}


async def simple_response_node(
    state: OrchestratorState,
    config: RunnableConfig,
) -> dict:
    """
    Simple response node for handling non-restaurant queries.

    This node generates responses for:
    - Greetings and welcomes
    - Thanks and acknowledgments
    - Questions about the assistant's capabilities
    - Off-topic redirections

    No tools are invoked - just a direct LLM response.

    Args:
        state: The orchestrator state containing messages.
        config: Runtime configuration with customer context.

    Returns:
        Updated state with the simple response.
    """
    observability = get_observability_manager()
    start_time = time.time()

    configurable = config.get("configurable", {})
    customer_name = configurable.get("customer_name", "Guest")
    intent = state.get("intent", "simple")

    messages = list(state["messages"])

    # Get the simple response chain
    simple_chain = get_simple_response_chain(customer_name=customer_name)

    with observability.create_span(
        "simple_response.generate",
        attributes={
            "intent": intent,
        },
    ):
        response = await simple_chain.ainvoke(
            {"messages": messages},
            config,
        )

    duration_ms = (time.time() - start_time) * 1000
    observability.record_workflow_step(
        step_name="simple_response",
        step_type="node",
        duration_ms=duration_ms,
        success=True,
        metadata={"intent": intent},
    )

    logger.debug(f"Simple response generated for intent: {intent}")

    return {"messages": response}


async def memory_post_hook(
    state: OrchestratorState,
    config: RunnableConfig,
) -> dict:
    """
    Post-hook node: Save the conversation turn to memory after processing.

    This triggers all memory strategies configured in the CDK stack:
    - Extracts and stores user preferences
    - Extracts semantic facts from the conversation
    - Updates conversation summaries

    Args:
        state: The orchestrator state containing messages.
        config: Runtime configuration with actor/session identifiers.

    Returns:
        Empty dict (no state changes, just side effects).
    """
    observability = get_observability_manager()
    start_time = time.time()

    configurable = config.get("configurable", {})
    actor_id = configurable.get("actor_id", "user:default")
    session_id = configurable.get("thread_id", "default_session")

    if state.get("response_status") != "approved":
        logger.debug("Response was not approved; skipping memory save")
        observability.add_span_event(
            "memory.skipped",
            attributes={"reason": "response_not_approved"},
        )
        return {}

    messages = state.get("messages", [])

    latest_user_index = next(
        (index for index in range(len(messages) - 1, -1, -1)
         if isinstance(messages[index], HumanMessage)),
        None,
    )
    latest_user = messages[latest_user_index] if latest_user_index is not None else None
    final_assistant = next(
        (
            msg
            for msg in reversed(messages[latest_user_index + 1 :])
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls
        ),
        None,
    ) if latest_user_index is not None else None

    user_input = _extract_text_content(latest_user.content) if latest_user else ""
    agent_response = _extract_text_content(final_assistant.content) if final_assistant else ""

    if not user_input or not agent_response or latest_user is None or final_assistant is None:
        logger.debug("Missing user input or agent response, skipping memory save")
        observability.add_span_event(
            "memory.skipped",
            attributes={"reason": "missing_input_or_response"}
        )
        return {}

    memory = get_memory_instance()
    event_time_text = latest_user.additional_kwargs.get("agentcore_event_timestamp")
    try:
        event_timestamp = (
            datetime.fromisoformat(event_time_text.replace("Z", "+00:00"))
            if isinstance(event_time_text, str)
            else datetime.now(timezone.utc)
        )
    except ValueError:
        event_timestamp = datetime.now(timezone.utc)

    user_message_id = latest_user.id or ""
    assistant_message_id = final_assistant.id or ""
    if not user_message_id:
        user_message_id = hashlib.sha256(user_input.encode("utf-8")).hexdigest()
    if not assistant_message_id:
        assistant_message_id = hashlib.sha256(agent_response.encode("utf-8")).hexdigest()

    try:
        with observability.create_span("memory.save"):
            result = await asyncio.to_thread(
                memory.process_turn,
                actor_id=actor_id,
                session_id=session_id,
                user_input=user_input,
                agent_response=agent_response,
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
                event_timestamp=event_timestamp,
            )

        duration_ms = (time.time() - start_time) * 1000
        if result.get("success"):
            observability.record_memory_operation("save", success=True, duration_ms=duration_ms)
            observability.record_workflow_step(
                step_name="memory_post_hook",
                step_type="node",
                duration_ms=duration_ms,
                success=True,
            )
        else:
            observability.record_memory_operation("save", success=False, duration_ms=duration_ms)
            observability.add_span_event(
                "memory.error",
                attributes={"error.type": result.get("error", "MemorySaveFailed")}
            )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        observability.record_memory_operation("save", success=False, duration_ms=duration_ms)
        logger.error(f"Memory post-hook failed: {type(e).__name__}")
        observability.add_span_event(
            "memory.exception",
            attributes={"error.type": type(e).__name__}
        )

    return {}
