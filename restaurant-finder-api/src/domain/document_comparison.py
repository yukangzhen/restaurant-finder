"""Server-owned contracts for a bounded, two-restaurant document comparison."""
from __future__ import annotations

from decimal import Decimal
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domain.document_rag import DocumentCitation, QuoteSelection, RetrievedEvidence

RowStatus = Literal["supported", "missing", "unavailable", "invalid"]
Reason = Literal["verified", "unsupported_price_format", "missing_evidence", "provider_error",
                 "deadline_exhausted", "invalid_evidence", "invalid_selection", "conflicting_evidence"]
ComparisonStatus = Literal["answered", "partial", "insufficient_evidence", "unavailable", "invalid_answer"]


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ComparisonPlan(StrictContract):
    restaurant_ids: tuple[str, str]
    item: str = Field(min_length=1, max_length=80)
    criterion: Literal["menu_item_price"] = "menu_item_price"
    generation_id: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def distinct(self):
        if len(set(self.restaurant_ids)) != 2 or any(
            not re.fullmatch(r"demo-[a-z0-9-]+", value) or len(value) > 128 for value in self.restaurant_ids
        ):
            raise ValueError("Comparison requires two distinct catalog IDs")
        return self


class PriceFact(StrictContract):
    amount: Decimal = Field(ge=Decimal("0"), le=Decimal("99999999.99"), allow_inf_nan=False, decimal_places=2, max_digits=10)
    currency: Literal["MYR"] = "MYR"
    unit: Literal["serving", "bowl", "piece", "listed_item"]


class ComparisonRow(StrictContract):
    restaurant_id: str = Field(pattern=r"^demo-[a-z0-9-]+$", max_length=128)
    status: RowStatus
    reason: Reason
    retrieval_started: bool = False
    selection: QuoteSelection | None = None
    evidence: RetrievedEvidence | None = None
    price: PriceFact | None = None

    @model_validator(mode="after")
    def coherent(self):
        supported = self.status == "supported"
        if supported != (self.selection is not None and self.evidence is not None):
            raise ValueError("Row evidence/status mismatch")
        if not supported and any(value is not None for value in (self.selection, self.evidence, self.price)):
            raise ValueError("Unverified row cannot carry facts")
        reasons = {"supported": {"verified", "unsupported_price_format"},
                   "missing": {"missing_evidence"}, "unavailable": {"provider_error", "deadline_exhausted"},
                   "invalid": {"invalid_evidence", "invalid_selection", "conflicting_evidence"}}
        if self.reason not in reasons[self.status]:
            raise ValueError("Row reason/status mismatch")
        if supported:
            if not self.retrieval_started or self.evidence.restaurant_id != self.restaurant_id:
                raise ValueError("Supported row needs scoped retrieval")
            if self.selection.chunk_id != self.evidence.chunk_id:
                raise ValueError("Row chunk mismatch")
            if (self.price is not None) != (self.reason == "verified"):
                raise ValueError("Row price/reason mismatch")
        return self


class ComparisonResult(StrictContract):
    plan: ComparisonPlan
    rows: tuple[ComparisonRow, ComparisonRow]
    status: ComparisonStatus
    coverage: int = Field(ge=0, le=2)
    difference: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    cheaper_id: str | None = None
    calculation_reason: Literal["calculated", "tie", "incomplete_evidence", "unsupported_price_format",
                                "different_units", "invalid_evidence"]
    text: str = Field(min_length=1, max_length=15000)
    citations: list[DocumentCitation] = Field(default_factory=list, max_length=2)

    @model_validator(mode="after")
    def coherent(self):
        if tuple(row.restaurant_id for row in self.rows) != self.plan.restaurant_ids:
            raise ValueError("Results must match plan order exactly")
        supported = [row for row in self.rows if row.status == "supported"]
        if self.coverage != len(supported):
            raise ValueError("Coverage mismatch")
        if any(row.evidence.generation_id != self.plan.generation_id for row in supported):
            raise ValueError("Mixed comparison generations")
        invalid = any(row.status == "invalid" for row in self.rows)
        expected_status = ("invalid_answer" if invalid else "answered" if len(supported) == 2
                           else "partial" if supported else "unavailable" if any(
                               row.status == "unavailable" for row in self.rows) else "insufficient_evidence")
        if self.status != expected_status:
            raise ValueError("Comparison status mismatch")
        expected_citations = supported if self.status in {"answered", "partial"} else []
        if len(self.citations) != len(expected_citations):
            raise ValueError("Comparison citation coverage mismatch")
        for index, (citation, row) in enumerate(zip(self.citations, expected_citations), 1):
            if citation.label != f"Source {index}" or citation.generation_id != self.plan.generation_id:
                raise ValueError("Comparison citation order/generation mismatch")
            if any(getattr(citation, field) != getattr(row.evidence, field) for field in
                   ("chunk_id", "document_id", "source_hash", "version", "page", "section", "line_start", "line_end")):
                raise ValueError("Comparison citation/row mismatch")
        comparable = not invalid and len(supported) == 2 and all(row.price for row in supported)
        comparable = comparable and supported[0].price.unit == supported[1].price.unit
        if comparable:
            a, b = (row.price.amount for row in supported)
            expected_difference = abs(a - b)
            expected_cheaper = None if a == b else supported[0 if a < b else 1].restaurant_id
            if self.difference != expected_difference or self.cheaper_id != expected_cheaper:
                raise ValueError("Calculation differs from verified facts")
            if self.calculation_reason != ("tie" if a == b else "calculated"):
                raise ValueError("Calculation reason mismatch")
        elif self.difference is not None or self.cheaper_id is not None:
            raise ValueError("Unsupported comparison cannot carry a calculation")
        else:
            expected_reason = ("invalid_evidence" if invalid else "incomplete_evidence" if len(supported) < 2
                               else "unsupported_price_format" if any(row.price is None for row in supported)
                               else "different_units")
            if self.calculation_reason != expected_reason:
                raise ValueError("Unsupported calculation reason mismatch")
        return self
