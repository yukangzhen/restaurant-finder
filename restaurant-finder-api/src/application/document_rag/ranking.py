"""Pure bounded keyword ranking and fusion; scores are never factual confidence."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Sequence

from src.domain.document_rag import canonical_text

BM25_K1 = 1.2
BM25_B = 0.75
RRF_CONSTANT = 60
ALGORITHM_VERSION = "bm25-rrf-v1"


@dataclass(frozen=True)
class KeywordCandidate:
    key: str
    score: float


@dataclass(frozen=True)
class FusedCandidate:
    key: str
    score: float
    vector_rank: int | None
    keyword_rank: int | None


def validate_top_k(top_k: int) -> None:
    if type(top_k) is not int or not 1 <= top_k <= 5:
        raise ValueError("Hybrid top_k must be an integer from 1 to 5")


def tokenize(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", canonical_text(text).casefold())


def keyword_rank(question: str, passages: Sequence[tuple[str, str]], *, top_k=5,
                 guard: Callable[[], None] = lambda: None) -> tuple[KeywordCandidate, ...]:
    """BM25 statistics belong only to the caller's already scoped passage pool."""
    validate_top_k(top_k)
    guard()
    if len(passages) > 48:
        raise ValueError("Keyword pool exceeds manifest bound")
    keys = [key for key, _ in passages]
    if any(not isinstance(key, str) or not key for key in keys) or len(set(keys)) != len(keys):
        raise ValueError("Invalid or duplicate keyword key")
    terms = sorted(set(tokenize(question)))
    if not terms or not passages:
        return ()
    counts = []
    for _, text in passages:
        guard()
        counts.append(Counter(tokenize(text)))
    lengths = [sum(c.values()) for c in counts]
    average = sum(lengths) / len(lengths)
    if not average:
        return ()
    frequencies = {term: sum(term in c for c in counts) for term in terms}
    ranked = []
    for (key, _), counts_for_passage, length in zip(passages, counts, lengths):
        guard()
        parts = []
        for term in terms:
            frequency = counts_for_passage[term]
            if frequency:
                inverse = math.log1p((len(passages) - frequencies[term] + .5) / (frequencies[term] + .5))
                parts.append(inverse * frequency * (BM25_K1 + 1) /
                             (frequency + BM25_K1 * (1 - BM25_B + BM25_B * length / average)))
        score = math.fsum(parts)
        if not math.isfinite(score):
            raise ValueError("Invalid keyword score")
        if score > 0:
            ranked.append(KeywordCandidate(key, score))
    return tuple(sorted(ranked, key=lambda c: (-c.score, c.key))[:top_k])


def reciprocal_rank_fusion(vector_keys: Sequence[str], keyword_keys: Sequence[str], *, top_k=5,
                          guard: Callable[[], None] = lambda: None) -> tuple[FusedCandidate, ...]:
    """Return the whole bounded union. The retriever verifies it before final truncation."""
    validate_top_k(top_k)
    guard()
    for keys in (vector_keys, keyword_keys):
        if len(keys) > top_k or any(not isinstance(key, str) or not key for key in keys):
            raise ValueError("Invalid ranked candidate list")
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate key inside a ranked candidate list")
    vectors = {key: rank for rank, key in enumerate(vector_keys, 1)}
    keywords = {key: rank for rank, key in enumerate(keyword_keys, 1)}
    fused = []
    for key in sorted(vectors.keys() | keywords.keys()):
        guard()
        vr, kr = vectors.get(key), keywords.get(key)
        score = math.fsum(1 / (RRF_CONSTANT + rank) for rank in (vr, kr) if rank is not None)
        if not math.isfinite(score) or score <= 0:
            raise ValueError("Invalid fusion score")
        fused.append(FusedCandidate(key, score, vr, kr))
    return tuple(sorted(fused, key=lambda c: (-c.score, c.key)))
