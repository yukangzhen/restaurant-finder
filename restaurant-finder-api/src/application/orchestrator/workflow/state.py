from typing import Annotated, Literal, TypedDict

from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


# Intent types for routing decisions
IntentType = Literal["restaurant_search", "document_qa", "simple", "off_topic"]


class OrchestratorState(TypedDict):
    """
    State for the Orchestrator Agent with Router + ReAct pattern.

    Architecture:
        START → Router → [conditional edge based on intent]
                         ├── "simple" → Simple Response → Memory Hook → END
                         ├── "off_topic" → Simple Response → Memory Hook → END
                         └── "restaurant_search" → Orchestrator → Tools → ... → Memory Hook → END

    The ReAct (Reasoning + Acting) pattern interleaves reasoning and action:
    - Thought: Agent reasons about what to do next
    - Action: Agent calls a tool or provides final answer
    - Observation: System provides tool results
    """

    # Messages with reducer that appends new messages
    messages: Annotated[list[BaseMessage], add_messages]

    # Customer name for personalization
    customer_name: str

    # Intent classification for routing (set by router_node)
    intent: IntentType

    # Tool call tracking (for efficiency limits)
    tool_call_count: int  # Number of tool calls in current turn
    made_tool_calls: bool  # Whether any tool calls were made this turn

    # Final response state set only after the output guardrail approves/blocks.
    response_status: Literal["pending", "approved", "blocked"]
    rag_status: str | None
    rag_generation: str | None
    rag_pending_scope: str | None
    rag_approved_scope: str | None
    rag_retrieval_count: int
    last_approved_intent: IntentType | None
