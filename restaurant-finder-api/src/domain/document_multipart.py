"""Strict private contracts for a bounded mixed-document workflow."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, model_validator

from src.domain.document_comparison import PriceFact, StrictContract
from src.domain.document_rag import DocumentCitation, QuoteSelection, RetrievedEvidence, canonical_text

Criterion = Literal["menu_item_price", "cancellation_policy"]
Status = Literal["supported", "missing", "unavailable", "invalid"]
Reason = Literal["verified", "unsupported_price_format", "missing_evidence", "unsupported_policy_layout",
                 "provider_error", "deadline_exhausted", "invalid_evidence", "invalid_selection", "conflicting_evidence"]


class PlannerTaskDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    restaurant_id: StrictStr = Field(pattern=r"^demo-[a-z0-9-]+$", max_length=128)
    criterion: Criterion
    item: StrictStr | None = Field(default=None, min_length=1, max_length=80)

    @model_validator(mode="after")
    def typed_item(self):
        if (self.item is not None) != (self.criterion == "menu_item_price"):
            raise ValueError("Draft item does not match criterion")
        return self


class MultipartPlanDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tasks: tuple[PlannerTaskDraft, ...] = Field(min_length=2, max_length=4)


class MultipartTask(StrictContract):
    task_id: str = Field(pattern=r"^task-[1-4]$")
    restaurant_id: str = Field(pattern=r"^demo-[a-z0-9-]+$", max_length=128)
    restaurant_name: str = Field(min_length=1, max_length=200)
    criterion: Criterion
    item: str | None = Field(default=None, min_length=1, max_length=80)

    @property
    def document_type(self):
        return "menu" if self.criterion == "menu_item_price" else "policy"

    @property
    def identity(self):
        return self.restaurant_id, self.criterion, canonical_text(self.item).casefold() if self.item else None

    @model_validator(mode="after")
    def typed_item(self):
        if (self.item is not None) != (self.criterion == "menu_item_price"):
            raise ValueError("Task item does not match criterion")
        return self


class MultipartRequest(StrictContract):
    question: str = Field(min_length=1, max_length=1000)
    tasks: tuple[MultipartTask, ...] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def complete(self):
        if tuple(t.task_id for t in self.tasks) != tuple(f"task-{i}" for i in range(1, len(self.tasks)+1)):
            raise ValueError("Task IDs must be complete and ordered")
        if len({t.identity for t in self.tasks}) != len(self.tasks):
            raise ValueError("Duplicate task")
        ids = tuple(dict.fromkeys(t.restaurant_id for t in self.tasks))
        if not 1 <= len(ids) <= 2 or {t.criterion for t in self.tasks} != {"menu_item_price", "cancellation_policy"}:
            raise ValueError("Request requires one/two restaurants and mixed criteria")
        if {t.restaurant_id for t in self.tasks if t.criterion == "menu_item_price"} != set(ids):
            raise ValueError("Every requested restaurant requires a menu task")
        items = {t.item for t in self.tasks if t.item}
        if len(items) != 1:
            raise ValueError("Request requires one item")
        expected = tuple(sorted(self.tasks, key=lambda t: (ids.index(t.restaurant_id), t.criterion != "menu_item_price")))
        if self.tasks != expected:
            raise ValueError("Tasks must follow canonical scope order")
        return self


class MultipartPlan(MultipartRequest):
    generation_id: str = Field(pattern=r"^[a-f0-9]{64}$")


class MultipartTaskResult(StrictContract):
    task: MultipartTask
    status: Status
    reason: Reason
    retrieval_started: bool = False
    selection: QuoteSelection | None = None
    evidence: RetrievedEvidence | None = None
    price: PriceFact | None = None

    @model_validator(mode="after")
    def coherent(self):
        reasons = {"supported": {"verified", "unsupported_price_format"},
                   "missing": {"missing_evidence", "unsupported_policy_layout"},
                   "unavailable": {"provider_error", "deadline_exhausted"},
                   "invalid": {"invalid_evidence", "invalid_selection", "conflicting_evidence"}}
        if self.reason not in reasons[self.status]:
            raise ValueError("Task status/reason mismatch")
        if self.reason == "unsupported_policy_layout" and self.task.criterion != "cancellation_policy":
            raise ValueError("Policy layout reason requires a policy task")
        if self.status != "supported":
            if any(v is not None for v in (self.selection, self.evidence, self.price)):
                raise ValueError("Unverified task carries facts")
        else:
            if not self.retrieval_started or self.selection is None or self.evidence is None:
                raise ValueError("Supported task requires evidence")
            if (self.evidence.restaurant_id != self.task.restaurant_id or self.evidence.document_type != self.task.document_type
                    or self.evidence.chunk_id != self.selection.chunk_id):
                raise ValueError("Task evidence scope mismatch")
            if self.task.criterion == "cancellation_policy":
                if self.price is not None or self.reason != "verified":
                    raise ValueError("Policy task cannot carry numeric facts")
            elif (self.price is not None) != (self.reason == "verified"):
                raise ValueError("Menu price/reason mismatch")
        return self


class MultipartResult(StrictContract):
    plan: MultipartPlan
    rows: tuple[MultipartTaskResult, ...] = Field(min_length=2, max_length=4)
    status: Literal["answered", "partial", "insufficient_evidence", "unavailable", "invalid_answer"]
    supported: int = Field(ge=0, le=4)
    difference: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    cheaper_id: str | None = None
    text: str = Field(min_length=1, max_length=15000)
    citations: tuple[DocumentCitation, ...] = Field(default=(), max_length=4)

    @model_validator(mode="after")
    def coherent(self):
        if tuple(r.task for r in self.rows) != self.plan.tasks:
            raise ValueError("Result does not cover exact ordered plan")
        supported = [r for r in self.rows if r.status == "supported"]
        if self.supported != len(supported):
            raise ValueError("Result coverage mismatch")
        invalid = any(r.status == "invalid" for r in self.rows)
        expected = ("invalid_answer" if invalid else "answered" if len(supported) == len(self.rows) else "partial" if supported
                    else "unavailable" if any(r.status == "unavailable" for r in self.rows) else "insufficient_evidence")
        if self.status != expected:
            raise ValueError("Result status mismatch")
        cited = supported if self.status in {"answered", "partial"} else []
        if len(self.citations) != len(cited):
            raise ValueError("Result citation coverage mismatch")
        for i, (citation, row) in enumerate(zip(self.citations, cited), 1):
            if citation.label != f"Source {i}" or citation.generation_id != self.plan.generation_id:
                raise ValueError("Result citation order/generation mismatch")
            if row.evidence.generation_id != self.plan.generation_id or any(
                    getattr(citation, f) != getattr(row.evidence, f) for f in
                    ("document_id", "chunk_id", "source_hash", "version", "page", "section", "line_start", "line_end")):
                raise ValueError("Result citation/evidence mismatch")
        menus = [r for r in supported if r.task.criterion == "menu_item_price"]
        comparable = not invalid and len(menus) == 2 and all(r.price for r in menus)
        comparable = comparable and menus[0].price.currency == menus[1].price.currency and menus[0].price.unit == menus[1].price.unit
        if comparable:
            a, b = (r.price.amount for r in menus)
            cheaper = None if a == b else menus[0 if a < b else 1].task.restaurant_id
            if self.difference != abs(a-b) or self.cheaper_id != cheaper:
                raise ValueError("Calculation differs from verified menu facts")
        elif self.difference is not None or self.cheaper_id is not None:
            raise ValueError("Unsupported result carries arithmetic")
        return self
