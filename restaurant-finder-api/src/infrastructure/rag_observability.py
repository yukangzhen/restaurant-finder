"""RAG span boundary: record safe error types, never exception payloads."""
from contextlib import contextmanager
from src.infrastructure.observability import get_observability_manager
from src.domain.document_rag import EvidenceIntegrityError


@contextmanager
def rag_span(name, attributes=None):
    with get_observability_manager().create_span(name, attributes=attributes or {}) as span:
        try:
            yield span
        except Exception as error:
            # Validation/provider errors can include document/model text in their repr.
            if isinstance(error, (EvidenceIntegrityError, TimeoutError)):
                raise type(error)(type(error).__name__) from None
            raise RuntimeError(type(error).__name__) from None
