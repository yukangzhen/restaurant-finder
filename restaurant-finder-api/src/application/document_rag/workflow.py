"""A bounded document workflow with exact-quote selection and deterministic citations."""
from __future__ import annotations
import asyncio
import html
import json
import re
import time

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.config import settings
from src.domain.document_rag import QueryRewrite, RagAnswerDraft, RagOutcome, canonical_text
from src.domain.prompts import RAG_ANSWER_PROMPT, RAG_QUERY_PROMPT
from src.application.document_rag.retrieval import DocumentRetriever, is_followup, resolve_query
from src.infrastructure.document_store import DocumentStore
from src.infrastructure.embeddings import TitanEmbeddings
from src.infrastructure.vector_store import VectorStore
from src.infrastructure.model import ModelType, extract_text_content, get_model
from src.infrastructure.observability import get_observability_manager
from src.infrastructure.rag_observability import rag_span


def structured_chain(prompt, schema, max_tokens):
    model = get_model(temperature=0, model_type=ModelType.EXTRACTION).model_copy(update={"max_tokens": max_tokens})
    return ChatPromptTemplate.from_messages([SystemMessage(content=prompt.prompt), ("human", "{payload}")]) | model.with_structured_output(schema)


def safe_markdown(text: str) -> str:
    # Escape controls, Markdown links/images/code/formatting, and raw HTML.
    text = "".join(c for c in text if c.isprintable() or c == " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", html.escape(text, quote=True))


def render_answer(draft: RagAnswerDraft, evidence: list) -> str:
    if draft.status == "insufficient_evidence":
        return "The active documents do not contain enough evidence to answer that question."
    by_id = {e.chunk_id: e for e in evidence}
    lines = ["According to the fictional demo documents:"]
    for selection in draft.selections:
        source = by_id.get(selection.chunk_id)
        quote = canonical_text(selection.quote)
        if source is None or not quote or quote not in source.text:
            raise ValueError("Quote is not an exact substring of verified evidence")
        # Document instructions are data. Do not display an instruction passage as an answer.
        if re.search(r"ignore (?:all |previous |the )?(?:instructions|rules)|system prompt|reveal (?:the )?secret|<script|javascript:", quote, re.I):
            raise ValueError("Instruction-like quote is not valid answer evidence")
        location = f"page {source.page}" if source.page else f"section {source.section}, lines {source.line_start}-{source.line_end}"
        citation = f"{source.restaurant_name}; {source.document_id}; {location}; version {source.version}; generation {source.generation_id[:12]}"
        lines.extend(["", f'> "{safe_markdown(quote)}"', "", f"Source: {safe_markdown(citation)}"])
    return "\n".join(lines)


def make_retriever():
    if settings.RAG_EMBEDDING_MODEL_ID != "amazon.titan-embed-text-v2:0" or settings.RAG_EMBEDDING_DIMENSIONS != 512:
        raise ValueError("RAG requires Titan V2 with 512 dimensions")
    return DocumentRetriever(DocumentStore(settings.RAG_DOCUMENT_BUCKET, settings.AWS_REGION),
                             VectorStore(settings.RAG_VECTOR_INDEX_ARN, settings.AWS_REGION),
                             TitanEmbeddings(settings.AWS_REGION, max_attempts=1), active_key=settings.RAG_ACTIVE_MANIFEST_KEY,
                             top_k=settings.RAG_TOP_K, max_characters=settings.RAG_MAX_CONTEXT_CHARACTERS)


async def answer_document_question(state, config, retriever=None, query_chain=None, answer_chain=None):
    if not settings.DOCUMENT_RAG_ENABLED:
        return RagOutcome(status="disabled", text="Document answering is currently disabled.")
    obs = get_observability_manager()
    question = next((extract_text_content(m.content) for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")
    retriever = retriever or make_retriever()
    with rag_span("rag.scope"):
        manifest = await asyncio.to_thread(retriever.pin)
        query = resolve_query(question, manifest, state.get("rag_approved_scope"))
        if query.clarification:
            return RagOutcome(status="clarify", text=query.clarification, generation_id=manifest.generation_id)
        # Explicit scope is resolved by server code first. The model may rewrite text only.
        if is_followup(question) and state.get("rag_approved_scope"):
            previous = next((extract_text_content(m.content)[:1200] for m in reversed(state["messages"][:-1]) if isinstance(m, AIMessage) and not m.tool_calls), "")
            chain = query_chain or structured_chain(RAG_QUERY_PROMPT, QueryRewrite, 400)
            rewrite = await chain.ainvoke({"payload": json.dumps({"question": question, "resolved_restaurant": query.restaurant_id,
                                            "previous_approved_answer": previous}, ensure_ascii=False)}, config)
            rewrite = QueryRewrite.model_validate(rewrite)
            # Rewriting cannot change the restaurant/type filter or introduce a source key.
            query = query.model_copy(update={"query": rewrite.query})
    with rag_span("rag.retrieve", attributes={"rag.generation": manifest.generation_id, "rag.restaurant": query.restaurant_id,
                                                    "rag.top_k": retriever.top_k}) as span:
        evidence = await asyncio.to_thread(retriever.retrieve, query, manifest)
        if span:
            span.set_attribute("rag.passages", len(evidence))
            span.set_attribute("rag.context_characters", sum(len(e.text) for e in evidence))
    if not evidence:
        return RagOutcome(status="insufficient_evidence", text="The active documents do not contain enough evidence to answer that question.",
                          generation_id=manifest.generation_id, restaurant_id=query.restaurant_id, retrieval_count=1)
    with rag_span("rag.answer_select", attributes={"prompt.name": RAG_ANSWER_PROMPT.name,
          "prompt.version": (RAG_ANSWER_PROMPT.bedrock_metadata or {}).get("version", "local")}) :
        chain = answer_chain or structured_chain(RAG_ANSWER_PROMPT, RagAnswerDraft, 1600)
        try:
            draft = await chain.ainvoke({"payload": json.dumps({"question": query.query, "evidence": [
                {"chunk_id": e.chunk_id, "text": e.text} for e in evidence]}, ensure_ascii=False)}, config)
            draft = RagAnswerDraft.model_validate(draft)
            with rag_span("rag.validate", attributes={"rag.quote_count": len(draft.selections)}):
                text = render_answer(draft, evidence)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.warning("RAG answer rejected (error_type={})", type(error).__name__)
            obs.add_span_event("rag.answer.rejected", attributes={"error.type": type(error).__name__})
            return RagOutcome(status="invalid_answer", text="I couldn't validate a document answer. Please rephrase your question.",
                              generation_id=manifest.generation_id, restaurant_id=query.restaurant_id, retrieval_count=1)
    return RagOutcome(status=draft.status, text=text, generation_id=manifest.generation_id,
                      restaurant_id=query.restaurant_id, retrieval_count=1)


async def document_qa_node(state, config):
    started = time.monotonic()
    try:
        async with asyncio.timeout(settings.RAG_REQUEST_TIMEOUT_SECONDS):
            outcome = await answer_document_question(state, config)
    except asyncio.CancelledError:
        raise
    except Exception as error:
        logger.warning("RAG retrieval unavailable (error_type={})", type(error).__name__)
        get_observability_manager().add_span_event("rag.unavailable", attributes={"error.type": type(error).__name__})
        outcome = RagOutcome(status="unavailable", text="Document retrieval is temporarily unavailable. Please try again later.")
    get_observability_manager().record_workflow_step(step_name="document_qa", step_type="node",
        duration_ms=(time.monotonic()-started)*1000, success=outcome.status not in {"unavailable", "invalid_answer"},
        metadata={"rag.status": outcome.status, "rag.generation": outcome.generation_id or "none", "rag.retrieval_count": outcome.retrieval_count})
    return {"messages": AIMessage(content=outcome.text, additional_kwargs={"document_rag_response":True}), "rag_status": outcome.status, "rag_generation": outcome.generation_id,
            "rag_pending_scope": outcome.restaurant_id if outcome.status in {"answered", "insufficient_evidence"} else None,
            "rag_retrieval_count": outcome.retrieval_count}
