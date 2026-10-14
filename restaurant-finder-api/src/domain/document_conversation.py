"""Strict private contracts for approved document conversation context."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Operation = Literal["cancellation_fee", "cancellation_policy", "menu_item_price", "price_comparison", "price_and_policy"]


class PrivateContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class DocumentContextDraft(PrivateContract):
    restaurant_ids: tuple[str, ...] = Field(min_length=1, max_length=2)
    item: str | None = Field(default=None, min_length=1, max_length=80)
    origin_mode: Literal["single", "comparison", "multipart"]
    generation_id: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent(self):
        from src.domain.document_rag import canonical_text
        if len(set(self.restaurant_ids)) != len(self.restaurant_ids) or any(
                not re.fullmatch(r"demo-[a-z0-9-]{1,123}", value) for value in self.restaurant_ids):
            raise ValueError("Invalid context targets")
        if self.origin_mode == "single" and len(self.restaurant_ids) != 1:
            raise ValueError("Single context requires one target")
        if self.origin_mode == "comparison" and len(self.restaurant_ids) != 2:
            raise ValueError("Comparison context requires two targets")
        if self.origin_mode != "single" and self.item is None:
            raise ValueError("Planned context requires an item")
        if self.item is not None and (self.item != canonical_text(self.item).casefold()
                or not all(c.isalnum() or c in " '-" for c in self.item)
                or re.search(r"\b(and|or|cancellation|parking|polic(?:y|ies)|allergies|ingredients)\b", self.item)):
            raise ValueError("Invalid context item")
        return self


class SealFields(PrivateContract):
    schema_version: Literal[1] = 1
    actor_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    thread_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    human_message_id: str = Field(min_length=1, max_length=100)
    ai_message_id: str = Field(min_length=1, max_length=100)
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("schema_version", mode="before")
    @classmethod
    def exact_version(cls, value):
        if type(value) is not int or value != 1:
            raise ValueError("Unsupported context schema version")
        return value

    @model_validator(mode="after")
    def check_seal(self):
        from src.domain.document_rag import digest
        if type(self.schema_version) is not int or any(
                not c.isprintable() for c in self.human_message_id + self.ai_message_id):
            raise ValueError("Invalid context producer")
        if digest(self.model_dump(mode="json", exclude={"payload_digest"})) != self.payload_digest:
            raise ValueError("Context payload differs from its seal")
        return self


class DocumentConversationContext(DocumentContextDraft, SealFields):
    pass


class DocumentFollowupDraft(PrivateContract):
    operation: Literal["cancellation_fee", "cancellation_policy", "menu_item_price", "price_and_policy"]
    candidate_ids: tuple[str, str]
    item: str | None = Field(default=None, min_length=1, max_length=80)
    context_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent(self):
        # Reuse the exact target/item grammar without giving a clarification facts.
        DocumentContextDraft(restaurant_ids=self.candidate_ids, item=self.item or "placeholder",
                             origin_mode="comparison", generation_id="0" * 64)
        if (self.item is not None) != (self.operation in {"menu_item_price", "price_and_policy"}):
            raise ValueError("Clarification item differs from operation")
        return self


class PendingDocumentFollowup(DocumentFollowupDraft, SealFields):
    pass


class FollowupResolution(PrivateContract):
    decision: Literal["not_applicable", "resolved", "clarify"]
    reason: Literal["not_applicable", "no_context", "ambiguous_venue", "resumed", "explicit_venue", "resolved",
                    "unsupported", "invalid_context", "unknown_venue", "missing_item", "expired_clarification"]
    operation: Operation | None = None
    restaurant_ids: tuple[str, ...] = Field(default=(), max_length=2)
    item: str | None = Field(default=None, min_length=1, max_length=80)
    effective_question: str | None = Field(default=None, min_length=1, max_length=1000)
    clarification: str | None = Field(default=None, min_length=1, max_length=1000)
    pending: DocumentFollowupDraft | None = None

    @property
    def mode(self):
        return "comparison" if self.operation == "price_comparison" else "multipart" if self.operation == "price_and_policy" else "single"

    @model_validator(mode="after")
    def coherent(self):
        if self.decision == "resolved":
            if self.operation is None or not self.restaurant_ids or not self.effective_question or self.clarification or self.pending:
                raise ValueError("Incomplete resolved request")
            if (self.item is not None) != (self.operation in {"menu_item_price", "price_comparison", "price_and_policy"}):
                raise ValueError("Resolved item differs from operation")
            expected_count = 2 if self.operation == "price_comparison" else 1 if self.operation != "price_and_policy" else len(self.restaurant_ids)
            if len(self.restaurant_ids) != expected_count:
                raise ValueError("Resolved operation differs from targets")
        elif self.decision == "clarify":
            if not self.clarification or self.effective_question or self.restaurant_ids or self.item:
                raise ValueError("Invalid clarification")
        elif any((self.operation, self.restaurant_ids, self.item, self.effective_question, self.clarification, self.pending)):
            raise ValueError("Unrecognized request cannot carry scope")
        return self
