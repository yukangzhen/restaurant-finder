"""
Short-term memory manager using AgentCore Memory.

Memory is created and configured via CDK infrastructure (agentcore-stack.ts).
The MEMORY_ID environment variable must be set from the CDK stack output.

Memory strategies are defined in the CDK stack:
- UserPreferenceStrategy: /users/{actorId}/preferences
- SemanticStrategy: /conversations/{actorId}/facts
- SummaryStrategy: /conversations/{sessionId}/summaries
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

import boto3
from langgraph_checkpoint_aws import AgentCoreMemorySaver
from loguru import logger

from src.config import settings


# Singleton instance for application-wide use
_memory_instance: "ShortTermMemory | None" = None
@dataclass
class MemoryRetrievalResult:
    """Memory records and per-category failures from a retrieval attempt."""

    memories: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


def get_memory_instance() -> "ShortTermMemory":
    """Get or create the shared ShortTermMemory singleton instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ShortTermMemory()
    return _memory_instance


class ShortTermMemory:
    """
    Short-term memory manager using AgentCore Memory.

    The MEMORY_ID must be provided via environment variable.
    Memory creation is handled by CDK infrastructure, not at runtime.
    """

    def __init__(self):
        if not settings.MEMORY_ID:
            raise RuntimeError(
                "MEMORY_ID environment variable is required. "
                "Deploy the CDK stack and set MEMORY_ID from the stack output."
            )

        self._memory_id = settings.MEMORY_ID
        self._client = boto3.client(
            "bedrock-agentcore", region_name=settings.AWS_REGION
        )
        logger.info(f"Using MEMORY_ID from environment: {self._memory_id}")

    @property
    def memory_id(self) -> str:
        """Return the configured memory ID."""
        return self._memory_id

    def get_memory(self) -> AgentCoreMemorySaver:
        """Get the LangGraph checkpointer for state persistence."""
        return AgentCoreMemorySaver(
            memory_id=self._memory_id,
            region_name=settings.AWS_REGION
        )

    def _retrieve_from_namespace(
        self,
        namespace: str,
        query: str,
        top_k: int,
        category: str,
    ) -> tuple[str, list[dict[str, Any]], str | None]:
        """Helper to retrieve memories from a single namespace."""
        try:
            response = self._client.retrieve_memory_records(
                memoryId=self._memory_id,
                namespace=namespace,
                searchCriteria={"searchQuery": query, "topK": top_k},
            )
            results = response.get("memoryRecordSummaries", [])
            logger.debug(f"Retrieved {len(results)} {category}")
            return category, results, None
        except Exception as e:
            logger.warning(f"Failed to retrieve memory category {category}: {type(e).__name__}")
            return category, [], type(e).__name__

    def retrieve_memories(
        self,
        query: str,
        actor_id: str,
        session_id: str,
        top_k: int = 5,
    ) -> MemoryRetrievalResult:
        """
        Retrieve all memory types before processing user input.

        Retrieves in parallel from:
        - User preferences (personalization data)
        - Semantic facts (conversation history facts)
        - Conversation summaries (session-based)

        Args:
            query: The user's input message to search against
            actor_id: The user/actor identifier
            session_id: The conversation session identifier
            top_k: Number of results to retrieve per namespace

        Returns:
            Memory records plus explicit per-category errors.
        """
        return self.retrieve_specific_memories(
            query=query,
            actor_id=actor_id,
            session_id=session_id,
            memory_types=["preferences", "facts", "summaries"],
            top_k=top_k,
        )

    def retrieve_specific_memories(
        self,
        query: str,
        actor_id: str,
        session_id: str,
        memory_types: list[str],
        top_k: int = 5,
    ) -> MemoryRetrievalResult:
        """
        Retrieve specific memory types in parallel.

        This method allows selective retrieval of memory types for efficiency.
        Memory types are retrieved in parallel for speed optimization.

        Available memory types:
        - "preferences": User preferences (dietary restrictions, favorite cuisines, etc.)
        - "facts": Semantic facts extracted from conversation history
        - "summaries": Conversation summaries from the current session

        Args:
            query: The user's input message to search against
            actor_id: The user/actor identifier
            session_id: The conversation session identifier
            memory_types: List of memory types to retrieve (e.g., ["preferences", "facts"])
            top_k: Number of results to retrieve per namespace

        Returns:
            Memory records plus explicit per-category errors.
        """
        retrieved = MemoryRetrievalResult()

        # Map memory types to their namespaces
        type_to_namespace = {
            "preferences": f"/users/{actor_id}/preferences",
            "facts": f"/conversations/{actor_id}/facts",
            "summaries": f"/conversations/{session_id}/summaries",
        }

        # Filter to only requested memory types
        retrieval_tasks = [
            (type_to_namespace[mem_type], mem_type)
            for mem_type in memory_types
            if mem_type in type_to_namespace
        ]

        if not retrieval_tasks:
            logger.warning(f"No valid memory types specified: {memory_types}")
            return retrieved

        # Execute all retrievals in parallel
        with ThreadPoolExecutor(max_workers=len(retrieval_tasks)) as executor:
            futures = {
                executor.submit(
                    self._retrieve_from_namespace,
                    namespace,
                    query,
                    top_k,
                    category,
                ): category
                for namespace, category in retrieval_tasks
            }

            for future in as_completed(futures):
                try:
                    category, results, error = future.result()
                    retrieved.memories[category] = results
                    if error:
                        retrieved.errors[category] = error
                except Exception as e:
                    category = futures[future]
                    logger.warning(
                        f"Parallel memory retrieval failed for {category}: {type(e).__name__}"
                    )
                    retrieved.memories[category] = []
                    retrieved.errors[category] = type(e).__name__

        return retrieved

    def process_turn(
        self,
        actor_id: str,
        session_id: str,
        user_input: str,
        agent_response: str,
        user_message_id: str,
        assistant_message_id: str,
        event_timestamp: datetime,
    ) -> dict[str, Any]:
        """
        Post-hook: Process and save the conversation turn to memory.

        This triggers all memory strategies configured in CDK:
        - User preference extraction and storage
        - Semantic fact extraction
        - Conversation summarization

        Args:
            actor_id: The user/actor identifier
            session_id: The conversation session identifier
            user_input: The user's message
            agent_response: The agent's response

        Returns:
            Dictionary with processing results
        """
        try:
            if event_timestamp.tzinfo is None:
                event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)
            event_timestamp = event_timestamp.astimezone(timezone.utc)
            idempotency_material = json.dumps(
                [actor_id, session_id, user_message_id, assistant_message_id],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            client_token = hashlib.sha256(idempotency_material.encode("utf-8")).hexdigest()

            event_info = self._client.create_event(
                memoryId=self._memory_id,
                actorId=actor_id,
                sessionId=session_id,
                eventTimestamp=event_timestamp,
                clientToken=client_token,
                payload=[
                    {
                        "conversational": {
                            "role": "USER",
                            "content": {"text": user_input},
                        }
                    },
                    {
                        "conversational": {
                            "role": "ASSISTANT",
                            "content": {"text": agent_response},
                        }
                    },
                ],
            )
            logger.info("Saved completed conversation turn to AgentCore Memory")
            return {
                "success": True,
                "retrieved_memories": [],
                "event_info": event_info,
            }
        except Exception as e:
            logger.error(f"Failed to save conversation turn: {type(e).__name__}")
            return {
                "success": False,
                "error": f"AgentCore Memory event creation failed ({type(e).__name__}).",
            }
