import asyncio
import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from test_document_rag_ingestion import CORPUS
from src.application.document_rag.ingestion import prepare_generation
from src.application.document_rag import workflow
from src.application.orchestrator import streaming
from src.application.orchestrator.workflow import nodes
from src.domain.document_rag import DocumentCitation, RagAnswerDraft, RagOutcome, RetrievedEvidence
from src.infrastructure import streaming as sse
from src.infrastructure.guardrails import GuardrailResult


class CitationTests(unittest.TestCase):
    def setUp(self):
        self.manifest, _ = prepare_generation(CORPUS)
        chunk = next(c for c in self.manifest.chunks if c.document_id == "harbor-menu")
        self.evidence = RetrievedEvidence(**{k:v for k,v in chunk.model_dump().items() if k != "key"},
            generation_id=self.manifest.generation_id, distance=.1, restaurant_name="Harbor Pasta Lab")
        self.draft = RagAnswerDraft(status="answered", selections=[{"chunk_id":chunk.chunk_id, "quote":"Mushroom pasta - RM28 per serving."}])
        self.text, self.citations = workflow.render_document_answer(self.draft, [self.evidence], self.manifest)

    def test_original_reference_and_label_match_the_pinned_manifest(self):
        source = next(s for s in self.manifest.sources if s.document_id == "harbor-menu")
        citation = self.citations[0]
        self.assertIn("Source: Source 1 — ", self.text)
        self.assertEqual(citation.source_hash, source.source_hash)
        self.assertEqual(citation.generation_id, self.manifest.generation_id)
        self.assertEqual((citation.filename,citation.format,citation.page), ("harbor-menu.pdf","pdf",1))
        self.assertEqual(citation.chunk_id, self.evidence.chunk_id)

    def test_labels_for_three_locations_are_deterministic_and_bounded(self):
        draft = self.draft.model_copy(update={"selections": self.draft.selections * 3})
        text, citations = workflow.render_document_answer(draft, [self.evidence], self.manifest)
        self.assertEqual([c.label for c in citations], ["Source 1","Source 2","Source 3"])
        for citation in citations:
            self.assertEqual(text.count(f"Source: {citation.label} — "),1)
        with self.assertRaises(ValueError):
            RagOutcome(status="answered",text=text,generation_id=self.manifest.generation_id,citations=citations+[citations[0]])

    def test_wrong_generation_hash_document_and_location_rejected(self):
        for changes in [{"generation_id":"a"*64},{"source_hash":"a"*64},{"version":"other"},{"page":2},{"restaurant_id":"other"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                workflow.render_document_answer(self.draft, [self.evidence.model_copy(update=changes)], self.manifest)
        manifest = copy.deepcopy(self.manifest)
        next(s for s in manifest.sources if s.document_id == "harbor-menu").key = "rag/generations/other/sources/harbor-menu.pdf"
        with self.assertRaises(ValueError):
            workflow.render_document_answer(self.draft,[self.evidence],manifest)

    def test_contract_rejects_unsafe_extra_or_inconsistent_fields(self):
        data = self.citations[0].model_dump()
        for changes in [{"url":"https://fake"},{"document_id":"../other"},{"source_hash":"bad"},
                        {"filename":"../menu.pdf"},{"page":True},{"page":11},{"format":"html"},
                        {"line_start":1},{"version":"bad\nversion"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                DocumentCitation.model_validate({**data,**changes})

    def test_non_answer_outcomes_have_no_references(self):
        text, references = workflow.render_document_answer(RagAnswerDraft(status="insufficient_evidence"), [], self.manifest)
        self.assertEqual(references, [])
        self.assertIn("enough evidence", text)
        for status in ["clarify","insufficient_evidence","disabled","unavailable","invalid_answer"]:
            with self.subTest(status=status), self.assertRaises(ValueError):
                RagOutcome(status=status,text="safe",generation_id=self.manifest.generation_id,citations=self.citations)

    def state(self):
        return {"messages":[HumanMessage(content="Harbor menu?"),AIMessage(content=self.text,id="answer")],
                "intent":"document_qa","rag_status":"answered", "rag_generation":self.manifest.generation_id,
                "rag_pending_citations":[c.model_dump() for c in self.citations],"rag_approved_citations":[{"stale":True}]}

    def test_only_unchanged_approved_document_answer_publishes_references(self):
        for allowed, output in [(True,self.text),(True,"masked answer"),(False,"")]:
            with self.subTest(allowed=allowed,output=output), patch.object(nodes,"apply_output_guardrail",return_value=GuardrailResult(allowed,output,"NONE")):
                result = asyncio.run(nodes.output_guardrail_node(self.state(),{}))
            self.assertEqual(result["rag_pending_citations"],[])
            self.assertEqual(bool(result["rag_approved_citations"]),allowed and output == self.text)
            self.assertEqual(result["messages"].additional_kwargs,{})
        state = self.state()
        state["intent"] = "simple"
        with patch.object(nodes,"apply_output_guardrail",return_value=GuardrailResult(True,self.text,"NONE")):
            self.assertEqual(asyncio.run(nodes.output_guardrail_node(state,{}))["rag_approved_citations"],[])

    def test_transient_references_reset_on_every_turn_and_return_only_approved(self):
        for status in ["approved","blocked"]:
            fake=SimpleNamespace(ainvoke=AsyncMock(return_value={**self.state(),"response_status":status,
                "rag_approved_citations":[c.model_dump() for c in self.citations]}))
            with patch.object(streaming,"create_orchestrator_graph",return_value=fake):
                turn=asyncio.run(streaming.run_orchestrator_turn("Harbor menu?",conversation_id="citation-offline",actor_id="citation-demo"))
            data=fake.ainvoke.await_args.kwargs["input"]
            self.assertEqual(data["rag_pending_citations"],[])
            self.assertEqual(data["rag_approved_citations"],[])
            self.assertEqual(bool(turn.citations),status == "approved")

    def test_one_sse_envelope_pairs_approved_text_and_metadata(self):
        async def collect():
            return [json.loads(e.removeprefix("data: ")) async for e in sse.stream_response("menu?",conversation_id="citation-offline",actor_id="citation-demo")]
        for blocked in [False,True]:
            turn=streaming.TurnResult(self.text,blocked,tuple(self.citations))
            with patch.object(sse,"apply_input_guardrail",return_value=GuardrailResult(True,"menu?","NONE")),\
                 patch.object(sse,"run_orchestrator_turn",new=AsyncMock(return_value=turn)) as run:
                events=asyncio.run(collect())
            run.assert_awaited_once()
            self.assertEqual(events[-1],{"done":True})
            self.assertEqual(len(events),2)
            if blocked:
                self.assertNotIn("citations",events[0])
            else:
                self.assertEqual(events[0],{"chunk":self.text,"citations":[c.model_dump() for c in self.citations]})


if __name__ == "__main__":
    unittest.main()
