"""Execute real RAG code with explicitly simulated external dependencies."""
from __future__ import annotations

import asyncio
import copy
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from src.domain.document_rag import ActivePointer, canonical_text
from src.evaluation.rag import Calls, Observation


class MemoryStore:
    def __init__(self, manifest):
        self.pointer = ActivePointer(generation_id=manifest.generation_id,
            manifest_key=f"rag/generations/{manifest.generation_id}/manifest.json")
        self.data = {self.pointer.manifest_key: manifest.model_dump(),
                     **{chunk.key: chunk.model_dump(exclude={"key"}) for chunk in manifest.chunks}}

    def active(self, _key):
        return self.pointer, "offline"

    def read_json(self, key):
        return copy.deepcopy(self.data[key]), "offline"


class SimulatedEmbeddings:
    def __init__(self, config):
        self.config, self.attempts, self.tokens = config, 0, 0

    def embed(self, _text):
        self.attempts += 1
        return [1.0] + [0.0] * 511


class SimulatedVectors:
    """Manifest-order hits with real scope filters; no semantic similarity claim."""
    def __init__(self, manifest):
        self.manifest, self.attempts, self.document_type = manifest, 0, None

    def validate_index(self):
        return None

    def query(self, _vector, generation_id, restaurant_id, document_type, top_k):
        self.attempts += 1
        self.document_type = document_type
        return [{"key": f"{generation_id}:{chunk.chunk_id}", "distance": 0.1, "metadata": {
                    "generation_id": generation_id, "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id, "restaurant_id": chunk.restaurant_id,
                    "document_type": chunk.document_type}}
                for chunk in self.manifest.chunks if chunk.restaurant_id == restaurant_id
                and (document_type is None or chunk.document_type == document_type)][:top_k]


class ScriptedSelector:
    def __init__(self, script, manifest):
        self.script, self.manifest, self.attempts = script, manifest, 0

    async def ainvoke(self, data, _config):
        self.attempts += 1
        supplied = json.loads(data["payload"])["evidence"]
        chunks = {chunk.chunk_id: chunk for chunk in self.manifest.chunks}
        selections = []
        for scripted in self.script.selections:
            candidates = [item for item in supplied if chunks[item["chunk_id"]].document_id == scripted.document_id]
            if not candidates:
                raise ValueError("Script has no supplied source")
            selected = next((item for item in candidates if canonical_text(scripted.quote) in item["text"]), candidates[0])
            selections.append({"chunk_id": scripted.chunk_id_override or selected["chunk_id"], "quote": scripted.quote})
        return {"status": self.script.status, "selections": selections}


class ScriptedRewrite:
    def __init__(self, script):
        self.script, self.attempts = script, 0

    async def ainvoke(self, _data, _config):
        self.attempts += 1
        if self.script.rewrite is None:
            raise ValueError("Unexpected rewrite")
        return {"query": self.script.rewrite}


class NoTelemetry:
    @contextmanager
    def create_span(self, *_args, **_kwargs):
        yield None

    def add_span_event(self, *_args, **_kwargs):
        return None


@contextmanager
def cloud_clients_forbidden():
    """Fail and count accidental client creation, even if app code catches it."""
    with ExitStack() as stack:
        guards = [stack.enter_context(patch(target, side_effect=AssertionError("Live client forbidden in offline evaluation")))
                  for target in ("boto3.client", "boto3.session.Session.__init__",
                                 "boto3.session.Session.client", "botocore.session.Session.create_client")]
        yield
        if any(guard.called for guard in guards):
            raise AssertionError("Offline evaluation attempted a live client")


def run_offline(dataset, grounded):
    with cloud_clients_forbidden():
        from langchain_core.messages import AIMessage, HumanMessage
        from src.config import settings
        from src.application.document_rag import workflow
        from src.application.document_rag.retrieval import DocumentRetriever

        class RecordingRetriever(DocumentRetriever):
            def __init__(self, *args):
                super().__init__(*args)
                self.evidence = []

            def retrieve(self, *args):
                self.evidence = super().retrieve(*args)
                return self.evidence

        telemetry = NoTelemetry()
        with ExitStack() as stack:
            stack.enter_context(patch.object(settings, "DOCUMENT_RAG_ENABLED", True))
            stack.enter_context(patch.object(workflow, "get_observability_manager", return_value=telemetry))
            stack.enter_context(patch("src.infrastructure.rag_observability.get_observability_manager", return_value=telemetry))
            model_guard = stack.enter_context(patch.object(workflow, "structured_chain", side_effect=AssertionError("Live model forbidden")))
            retriever_guard = stack.enter_context(patch.object(workflow, "make_retriever", side_effect=AssertionError("Cloud retriever forbidden")))
            observations = []
            for case in dataset.cases:
                manifest, _ = grounded[case.id]
                embeddings, vectors = SimulatedEmbeddings(manifest.config), SimulatedVectors(manifest)
                retriever = RecordingRetriever(MemoryStore(manifest), vectors, embeddings)
                selector, rewrite = ScriptedSelector(case.simulation, manifest), ScriptedRewrite(case.simulation)
                state = {"messages": [AIMessage(content="Previous approved fictional document answer."), HumanMessage(content=case.question)],
                         "rag_approved_scope": case.approved_scope}
                outcome = asyncio.run(workflow.answer_document_question(state, {}, retriever, rewrite, selector))
                observations.append(Observation(case_id=case.id, origin="offline_simulated",
                    status=outcome.status, text=outcome.text, restaurant_id=outcome.restaurant_id,
                    generation_id=outcome.generation_id, citations=outcome.citations, evidence=retriever.evidence,
                    query_document_type=vectors.document_type,
                    calls=Calls(embedding=embeddings.attempts, retrieval=vectors.attempts,
                                selector=selector.attempts, rewrite=rewrite.attempts)))
            if model_guard.called or retriever_guard.called:
                raise AssertionError("Offline evaluation attempted a live dependency")
            return observations
