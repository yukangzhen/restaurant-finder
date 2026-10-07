"""Resolve and validate the actor and conversation identifiers for a request."""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass


_SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z")
_ACTOR_ID_PATTERN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9\-_/]*(?::[A-Za-z0-9\-_/]+)*[A-Za-z0-9\-_/]*\Z"
)


@dataclass(frozen=True)
class RequestIdentity:
    actor_id: str
    conversation_id: str


def resolve_request_identity(
    conversation_id: str | None,
    actor_id: str | None,
) -> RequestIdentity:
    """Validate supplied IDs and give anonymous requests isolated identities."""
    resolved_conversation_id = conversation_id or str(uuid.uuid4())
    if not isinstance(resolved_conversation_id, str) or not _SESSION_ID_PATTERN.fullmatch(
        resolved_conversation_id
    ):
        raise ValueError(
            "conversation_id must start with a letter or digit and contain only "
            "letters, digits, hyphens, or underscores (maximum 100 characters)."
        )

    if actor_id is not None:
        if not isinstance(actor_id, str) or len(actor_id) > 255 or not _ACTOR_ID_PATTERN.fullmatch(actor_id):
            raise ValueError("actor_id is not a valid AgentCore actor identifier.")
        resolved_actor_id = actor_id
    else:
        conversation_hash = hashlib.sha256(
            resolved_conversation_id.encode("utf-8")
        ).hexdigest()
        resolved_actor_id = f"anon:{conversation_hash}"

    return RequestIdentity(
        actor_id=resolved_actor_id,
        conversation_id=resolved_conversation_id,
    )
