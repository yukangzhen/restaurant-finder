"""Authored synthetic fixtures exercise real-source contracts; no restaurant originals in Git."""
import asyncio
import copy
import io
import json
from contextlib import ExitStack, contextmanager
from decimal import Decimal
from pathlib import Path
import threading
import time
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from src.application.document_rag import comparison, comparison_workflow, discovery, multipart, multipart_workflow, native_menu, workflow
from src.application.document_rag.ingestion import prepare_generation
from src.application.document_rag.retrieval import DocumentRetriever, router_catalog
from src.application.orchestrator import streaming
from src.application.orchestrator.workflow import graph, nodes
from src.config import settings
from src.deployment.prepare_real_demo import booking_snapshot
from src.domain.document_multipart import MultipartTask
from src.domain.document_rag import CorpusSpec, EvidenceIntegrityError, GenerationManifest, QuoteSelection, RagAnswerDraft, RetrievedEvidence, digest
from src.evaluation.rag_offline import MemoryStore, NoTelemetry, SimulatedEmbeddings, SimulatedVectors, cloud_clients_forbidden
from src.infrastructure.document_parser import extract_units
from src.infrastructure.guardrails import GuardrailResult

D1 = "Find two Italian restaurants in Kuala Lumpur that have menus in your document collection."
D2 = "Compare Margherita prices at Natalina and Nero Nero. Show the sources."
D3 = "What about both restaurants' prices and cancellation policies?"
D4 = "According to Natalina's documents, is valet parking available?"
N, R = "demo-natalina-kl", "demo-nero-nero-kl"
NOTE = "Prices exclude service charge 10% and SST 6%."
# Authored test wording, not a claim or transcription of either restaurant's policy.
POLICY = ("24-hour advance cancellation: no fee. Late notice: RM25 per person. "
          "No-show: RM25 per person. Date changes after the deadline incur the late fee.")


def pdf(lines, pages=1, text_page=1):
    writer = PdfWriter()
    for index in range(1, pages+1):
        page = writer.add_blank_page(width=600, height=800)
        if index != text_page:
            continue
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(("BT /F1 12 Tf 40 700 Td 16 TL\n" + "\n".join(
            "(" + s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") Tj T*" for s in lines) + "\nET").encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    result = io.BytesIO()
    writer.write(result)
    return result.getvalue()


def synthetic_corpus(root):
    venues = router_catalog(include_real=True)[-2:]
    specs = []
    for venue, stem, amount, page in [(venues[0], "natalina", 48, 6), (venues[1], "nero", 39, 9)]:
        body = pdf(["Synthetic native menu", "Pizza", f"Margherita {amount}", "Tomato and cheese.", "Next item 99", "Other dish.", NOTE], page, page)
        name = stem+".pdf"
        (root/name).write_bytes(body)
        provenance = dict(kind="official_pdf", origin_url=venue["website"]+"synthetic.pdf", resolved_url=venue["website"]+"synthetic.pdf",
            website_url=venue["website"], captured_at="2026-10-20T00:00:00Z", content_sha256=digest(body))
        specs.append(dict(document_id=stem+"-menu", restaurant_id=venue["restaurant_id"], path=name, version="synthetic-test",
            document_type="menu", provenance=provenance, native_menu=dict(records=[dict(item="Margherita", category="Pizza", page=page,
            start="Margherita", end="Next item", price_position="after_title", charge_note=NOTE)], decorative_pages=list(range(1,page)),
            currency="MYR", currency_source_url=venue["website"], currency_source_sha256="a"*64, currency_excerpt="Synthetic RM48 evidence")))
        url=f"https://www.sevenrooms.com/explore/{stem}/reservations/create/search/"
        policy=booking_snapshot("Synthetic test policy\n\nCancelation Policy:\n"+POLICY, url, "2026-10-20T00:00:00Z")
        (root/(stem+".md")).write_bytes(policy)
        specs.append(dict(document_id=stem+"-policy", restaurant_id=venue["restaurant_id"], path=stem+".md", version="synthetic-test",
            document_type="policy", provenance=dict(kind="booking_page_snapshot", origin_url=url, resolved_url=url,
            website_url=venue["website"], captured_at="2026-10-20T00:00:00Z", content_sha256=digest(policy))))
    corpus=dict(schema_version=2, fictional=False, restaurants=venues, documents=specs)
    (root/"corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
    return prepare_generation(root/"corpus.json")[0], corpus


def passages(manifest, rid, kind=None):
    name=next(r.name for r in manifest.restaurants if r.restaurant_id==rid)
    return [RetrievedEvidence(**c.model_dump(exclude={"key"}), generation_id=manifest.generation_id, restaurant_name=name)
        for c in manifest.chunks if c.restaurant_id==rid and (kind is None or c.document_type==kind)]


class LocalRetriever:
    def __init__(self, manifest, ledger=None):
        self.manifest, self.ledger = manifest, ledger
        self.store=self.vectors=self.embeddings=SimpleNamespace()
        self.top_k, self.max_characters=5,9000
    def pin(self, **kwargs):
        return self.manifest
    def retrieve(self, query, manifest, **kwargs):
        if self.ledger is not None:
            with self.ledger["lock"]:
                self.ledger["active"]+=1
                self.ledger["maximum"]=max(self.ledger["maximum"],self.ledger["active"])
                self.ledger["calls"].append((query.restaurant_id,query.document_type))
            time.sleep(.01)
            with self.ledger["lock"]:
                self.ledger["active"]-=1
        # Scope-aware synthetic retrieval; no semantic quality claim.
        return [p for p in passages(manifest,query.restaurant_id,query.document_type)
                if p.document_type=="menu" or p.section=="Cancelation Policy"][:5]


class HybridLocalRetriever(LocalRetriever):
    """Production ranking/integrity code with simulated semantic candidates."""
    def __init__(self, manifest, ledger=None):
        super().__init__(manifest,ledger)
        class Vectors(SimulatedVectors):
            def query(self,*args,**kwargs):
                return super().query(*args)
        from src.domain.document_rag import RagConfig
        self.embeddings=SimulatedEmbeddings(RagConfig()) # same default as actual Titan adapter
        self.store=MemoryStore(manifest)
        self.vectors=Vectors(manifest)
        self.delegate=DocumentRetriever(self.store,self.vectors,self.embeddings,retrieval_mode="hybrid")
    def pin(self,**kwargs):
        return self.delegate.pin(**kwargs)
    def retrieve(self,query,manifest,**kwargs):
        # Count worker concurrency independently of ranking quality.
        super().retrieve(query,manifest,**kwargs)
        return self.delegate.retrieve(query,manifest,**kwargs)


@contextmanager
def offline_real():
    with cloud_clients_forbidden(), ExitStack() as stack:
        for name in ("DOCUMENT_RAG_ENABLED","DOCUMENT_REAL_SOURCES_ENABLED","DOCUMENT_FOLLOWUPS_ENABLED","DOCUMENT_MULTIPART_ENABLED"):
            stack.enter_context(patch.object(settings,name,True))
        for target in ("src.infrastructure.rag_observability.get_observability_manager",
                       "src.application.document_rag.workflow.get_observability_manager",
                       "src.application.orchestrator.workflow.nodes.get_observability_manager"):
            telemetry=NoTelemetry()
            telemetry.record_workflow_step=lambda **kwargs:None
            telemetry.record_memory_operation=lambda *args,**kwargs:None
            stack.enter_context(patch(target,return_value=telemetry))
        yield


class RealSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.manifest,self.corpus=synthetic_corpus(self.root)

    def test_published_fixture_generation_stays_identical(self):
        manifest,_=prepare_generation(Path("sample_documents/corpus-v2.json"))
        self.assertEqual(manifest.generation_id,"29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a")
        self.assertEqual(len(router_catalog(include_real=False)),3)
        self.assertEqual(len(router_catalog(include_real=True)),5)

    def test_original_hash_provenance_and_schema_cannot_be_reinterpreted(self):
        for mutate in (lambda x:x.update(schema_version=1),
                       lambda x:x["sources"][0]["provenance"].update(captured_at="2026-10-21T00:00:00Z"),
                       lambda x:x["sources"][0]["provenance"].update(content_sha256="f"*64)):
            data=self.manifest.model_dump()
            mutate(data)
            with self.assertRaises(ValueError):
                GenerationManifest.model_validate(data)
        (self.root/"natalina.pdf").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError,"Original bytes"):
            prepare_generation(self.root/"corpus.json")

    def test_native_text_retains_page_numbers_and_requires_explicit_blank_pages(self):
        body=pdf(["Margherita 48"],12,12)
        units=extract_units(body,".pdf",decorative_pages=range(1,12))
        self.assertEqual([u.page for u in units],[12])
        with self.assertRaisesRegex(ValueError,"no extractable"):
            extract_units(body,".pdf")
        with self.assertRaisesRegex(ValueError,"1 to 12"):
            extract_units(pdf(["Margherita 48"],13,13),".pdf",decorative_pages=range(1,13))
        with self.assertRaisesRegex(ValueError,"outside the original"):
            extract_units(pdf(["Text"]),".pdf",decorative_pages=[2])

    def test_native_records_price_description_note_and_no_inferred_portion(self):
        evidence=passages(self.manifest,N,"menu")
        row=native_menu.registered_records("Margherita",N,evidence,self.manifest)[0]
        self.assertEqual(row.amount,Decimal("48"))
        self.assertEqual(row.quote,"Margherita 48 Tomato and cheese.")
        self.assertEqual(native_menu.price_fact(row).unit,"listed_item")
        draft=native_menu.native_draft("Margherita",N,evidence,self.manifest)
        text,citations=workflow.render_document_answer(draft,evidence,self.manifest)
        self.assertIn(workflow.safe_markdown(NOTE),text);self.assertNotIn("fictional",text)
        self.assertEqual(citations[0].page,6)
        self.assertEqual(native_menu.native_draft("Unknown",N,evidence,self.manifest).status,"insufficient_evidence")
        factless=copy.copy(row)
        object.__setattr__(factless,"currency",None)
        self.assertIsNone(native_menu.price_fact(factless))

    def test_split_native_title_expands_lookup_without_editing_quotes(self):
        from src.domain.document_rag import DocumentQuery
        corpus=copy.deepcopy(self.corpus)
        spec=corpus["documents"][0]
        body=pdf(["Synthetic native menu","Pizza","MARGHE RIT A 48","Tomato and cheese.","Next item 99","Other dish.",NOTE],6,6)
        spec["native_menu"]["records"][0]["start"]="MARGHE RIT A"
        spec["provenance"]["content_sha256"]=digest(body)
        (self.root/spec["path"]).write_bytes(body)
        (self.root/"split.json").write_text(json.dumps(corpus),encoding="utf-8")
        manifest,_=prepare_generation(self.root/"split.json")
        query=DocumentQuery(query="Margherita listed price at Natalina",restaurant_id=N,document_type="menu")
        lookup=native_menu.native_lookup_query(query,manifest)
        self.assertIn("MARGHE RIT A",lookup)
        self.assertEqual(native_menu.native_lookup_query(query.model_copy(update={"document_type":"policy"}),manifest),query.query)
        with offline_real():
            evidence=HybridLocalRetriever(manifest).retrieve(query,manifest)
        row=native_menu.registered_records("Margherita",N,evidence,manifest)[0]
        self.assertEqual(row.quote,"MARGHE RIT A 48 Tomato and cheese.")
        self.assertEqual(row.amount,Decimal("48"))

    def test_adjacent_price_partial_row_and_corrupted_passage_are_rejected(self):
        evidence=passages(self.manifest,N,"menu")
        for quote in ("Margherita 48","Next item 99 Other dish.","48","Margherita 99 Tomato and cheese."):
            with self.subTest(quote=quote), self.assertRaises(ValueError):
                comparison.validate_menu_selection("Margherita",self.manifest.generation_id,N,
                    RagAnswerDraft(status="answered",selections=[QuoteSelection(chunk_id=evidence[0].chunk_id,quote=quote)]),evidence,self.manifest)
        bad=evidence[0].model_copy(update={"text":evidence[0].text.replace("48","99")})
        with self.assertRaises(EvidenceIntegrityError):
            native_menu.registered_records("Margherita",N,[bad],self.manifest)

    def test_missing_charge_note_and_duplicate_category_fail_closed(self):
        # Mutations are deliberately invalid pinned test objects, never publishable manifests.
        manifest=self.manifest.model_copy(deep=True)
        manifest.sources[0].native_menu.records[0].charge_note="Missing charge note"
        with self.assertRaisesRegex(EvidenceIntegrityError,"charge note"):
            native_menu.registered_records("Margherita",N,passages(manifest,N,"menu"),manifest)
        manifest=self.manifest.model_copy(deep=True)
        anchor=manifest.sources[0].native_menu.records[0].model_copy(update={"category":"Synthetic native menu"})
        manifest.sources[0].native_menu.records.append(anchor)
        with self.assertRaisesRegex(EvidenceIntegrityError,"More than one"):
            native_menu.registered_records("Margherita",N,passages(manifest,N,"menu"),manifest)

    def test_complete_policy_cannot_lose_per_person_or_reschedule_conditions(self):
        task=MultipartTask(task_id="task-1",restaurant_id=N,restaurant_name="Natalina",criterion="cancellation_policy")
        evidence=passages(self.manifest,N,"policy")
        record,reason=multipart.policy_record(task,evidence,self.manifest)
        self.assertEqual(reason,"verified");self.assertEqual(record[1],POLICY)
        good=RagAnswerDraft(status="answered",selections=[QuoteSelection(chunk_id=record[0].chunk_id,quote=record[1])])
        self.assertEqual(multipart.validate_task_selection(task,good,evidence,self.manifest).status,"supported")
        for quote in ("24-hour advance cancellation: no fee.",POLICY.replace(" per person",""),POLICY.split("Date changes")[0].strip()):
            with self.assertRaises(ValueError):
                multipart.validate_task_selection(task,RagAnswerDraft(status="answered",selections=[QuoteSelection(chunk_id=record[0].chunk_id,quote=quote)]),evidence,self.manifest)

    def test_discovery_uses_real_search_sources_not_canned_results(self):
        async def search(**kwargs):
            venue=next(r for r in self.manifest.restaurants if r.name in kwargs["query"])
            return SimpleNamespace(status="success",restaurants=[],web_sources=[{"url":venue.website}])
        with offline_real():
            result=asyncio.run(discovery.discover_document_venues(D1,retriever=LocalRetriever(self.manifest),search=search))
        self.assertEqual(result.verified_count,2);self.assertEqual(result.search_attempts,2)
        self.assertIn("not a city-wide ranking",result.text)
        for venue in self.manifest.restaurants:
            self.assertIn(venue.name,result.text);self.assertIn(venue.website,result.text)
        for bad in ("https://example.com/","https://www.natalinakl.com.evil.test/","https://www.natalinakl.com/?token=secret"):
            self.assertIsNone(discovery.online_match(self.manifest.restaurants[0],SimpleNamespace(status="success",restaurants=[],web_sources=[{"url":bad}])))
        wrong=SimpleNamespace(name="Natalina",city="Penang",address=None,website=self.manifest.restaurants[0].website)
        self.assertIsNone(discovery.online_match(self.manifest.restaurants[0],SimpleNamespace(status="success",restaurants=[wrong],web_sources=[])))

    def test_discovery_budget_scope_and_failure_do_not_claim_success(self):
        search=AsyncMock(side_effect=RuntimeError("private provider details"))
        with offline_real():
            a=asyncio.run(discovery.discover_document_venues(D1,retriever=LocalRetriever(self.manifest),search=search,remaining_tools=1))
            b=asyncio.run(discovery.discover_document_venues(D1.replace("Kuala Lumpur","Penang"),retriever=LocalRetriever(self.manifest),search=search))
            self.assertEqual(search.await_count,0)
            c=asyncio.run(discovery.discover_document_venues(D1,retriever=LocalRetriever(self.manifest),search=search))
        self.assertEqual(c.search_attempts,2);self.assertEqual(c.verified_count,0)
        self.assertNotIn("private",c.text);self.assertIn("budget",a.text);self.assertIn("does not identify",b.text)

    def test_uncertain_discovery_send_is_counted_on_timeout(self):
        async def timeout(*args,attempts,**kwargs):
            attempts.append(N)
            raise TimeoutError()
        with offline_real(),patch.object(discovery,"discover_document_venues",side_effect=timeout):
            result=asyncio.run(discovery.coverage_discovery_node({"messages":[HumanMessage(content=D1)],"tool_call_count":1},{}))
        self.assertEqual(result["tool_call_count"],2);self.assertTrue(result["made_tool_calls"])
        self.assertIn("temporarily unavailable",result["messages"].content)

    def test_router_prioritizes_coverage_without_jev_and_keeps_fallback_for_documents(self):
        with offline_real(),patch.object(nodes,"classify_with_jev",new_callable=AsyncMock) as jev,patch.object(nodes,"get_router_chain") as fallback:
            result=asyncio.run(nodes.router_node({"messages":[HumanMessage(content=D1)]},{}))
        self.assertTrue(result["coverage_discovery_requested"]);jev.assert_not_awaited();fallback.assert_not_called()

    def test_real_document_bedrock_fallback_receives_same_catalog(self):
        from src.infrastructure.jev_router import JevRouterUnavailable
        from langchain_core.messages import AIMessage
        fallback=SimpleNamespace(ainvoke=AsyncMock(return_value=AIMessage(content="document_qa")))
        with offline_real(),patch.object(nodes,"classify_with_jev",side_effect=JevRouterUnavailable("offline")),patch.object(nodes,"get_router_chain",return_value=fallback):
            result=asyncio.run(nodes.router_node({"messages":[HumanMessage(content=D2)]},{"configurable":{"thread_id":"fallback","actor_id":"portfolio"}}))
        self.assertEqual(result["intent"],"document_qa")
        context=fallback.ainvoke.await_args.args[0]["router_context"]
        self.assertIn("document_catalog",context)
        self.assertIn(N,context);self.assertIn(R,context)
        self.assertFalse(result["coverage_discovery_requested"])

    def test_currency_requires_reviewed_proof_and_unknown_currency_withholds_arithmetic(self):
        from src.domain.document_rag import NativeMenuProfile
        data=self.manifest.sources[0].native_menu.model_dump()
        for changes in ({"currency_source_url":None},{"currency_source_sha256":None},{"currency_excerpt":"48"}):
            with self.assertRaises(ValueError):
                NativeMenuProfile.model_validate({**data,**changes})
        manifest=self.manifest.model_copy(deep=True)
        profile=manifest.sources[0].native_menu
        profile.currency=profile.currency_source_url=profile.currency_source_sha256=profile.currency_excerpt=None
        row=native_menu.registered_records("Margherita",N,passages(manifest,N,"menu"),manifest)[0]
        self.assertIsNone(native_menu.price_fact(row))

    def test_private_corpus_is_excluded_from_image_context(self):
        self.assertIn(".generated/real-restaurants*/",(Path(__file__).resolve().parents[1]/".dockerignore").read_text())

    def test_four_connected_turns_use_parent_approval_fresh_tasks_and_bounded_workers(self):
        self.run_connected(block_comparison=False)

    def test_blocked_comparison_cannot_publish_sources_or_advance_context(self):
        self.run_connected(block_comparison=True)

    def run_connected(self,block_comparison):
        ledger={"active":0,"maximum":0,"calls":[],"lock":threading.Lock()}
        retriever=lambda *_args:HybridLocalRetriever(self.manifest,ledger)
        selector=Mock(side_effect=AssertionError("Native selector must not call a model"))
        cmp=comparison_workflow.ComparisonDependencies(retriever,retriever,selector)
        request=multipart.compile_multipart_request("Compare Margherita prices at Natalina and Nero Nero, and explain both restaurants' cancellation policies.",self.manifest)
        draft={"tasks":[{"restaurant_id":t.restaurant_id,"criterion":t.criterion,"item":t.item} for t in request.tasks]}
        planner=SimpleNamespace(ainvoke=AsyncMock(return_value=draft))
        mp=multipart_workflow.MultipartDependencies(retriever,retriever,lambda:planner,selector)
        saver=InMemorySaver()
        saved=Mock(return_value={"success":True})
        async def search(**kwargs):
            venue=next(r for r in self.manifest.restaurants if r.name in kwargs["query"])
            return SimpleNamespace(status="success",restaurants=[],web_sources=[{"url":venue.website}])
        async def discover(question,**kwargs):
            return await original_discovery(question,retriever=retriever(),search=search,**kwargs)
        original_discovery=discovery.discover_document_venues
        moderated=[]
        def moderate(text,*args,**kwargs):
            moderated.append(text)
            allowed=not (block_comparison and "Listed prices in" in text)
            return GuardrailResult(allowed,text if allowed else "Blocked","NONE" if allowed else "GUARDRAIL_INTERVENED")
        abstain=SimpleNamespace(ainvoke=AsyncMock(return_value=RagAnswerDraft(status="insufficient_evidence")))
        with offline_real(),ExitStack() as stack:
            for target,value in [(graph,"_graph_instance"),]:
                stack.enter_context(patch.object(target,value,None))
            stack.enter_context(patch.object(graph,"get_orchestrator_tools",return_value=[]))
            stack.enter_context(patch.object(graph,"ShortTermMemory",return_value=SimpleNamespace(get_memory=lambda:saver)))
            compiled=graph.create_orchestrator_graph(force_recreate=True)
            stack.enter_context(patch.object(streaming,"create_orchestrator_graph",return_value=compiled))
            stack.enter_context(patch.object(nodes,"classify_with_jev",AsyncMock(return_value=SimpleNamespace(intent="document_qa",confidence=.99))))
            stack.enter_context(patch.object(nodes,"apply_output_guardrail",side_effect=moderate))
            stack.enter_context(patch.object(nodes,"get_memory_instance",return_value=SimpleNamespace(process_turn=saved)))
            stack.enter_context(patch.object(discovery,"discover_document_venues",side_effect=discover))
            stack.enter_context(patch.object(workflow,"make_retriever",side_effect=retriever))
            stack.enter_context(patch.object(workflow,"structured_chain",return_value=abstain))
            stack.enter_context(patch.object(comparison_workflow,"ComparisonDependencies",return_value=cmp))
            stack.enter_context(patch.object(multipart_workflow,"MultipartDependencies",return_value=mp))
            turns=[]
            for question in (D1,D2) if block_comparison else (D1,D2,D3,D4):
                result=asyncio.run(streaming.run_orchestrator_turn(question,conversation_id="real-demo-test",actor_id="portfolio"))
                turns.append(result)
                state=compiled.get_state({"configurable":{"thread_id":"real-demo-test","actor_id":"portfolio"}}).values
                if question==D1:
                    self.assertFalse(result.citations);self.assertFalse(state.get("rag_approved_context"))
                if question==D2:
                    if block_comparison:
                        self.assertTrue(result.blocked);self.assertFalse(result.citations);self.assertFalse(state.get("rag_approved_context"))
                        continue
                    self.assertEqual(len(result.citations),2)
                    self.assertIn("RM9 lower",result.text);self.assertNotIn("per serving",result.text)
                    self.assertEqual(tuple(state["rag_approved_context"]["restaurant_ids"]),(N,R))
                if question==D3:
                    self.assertEqual(len(result.citations),4);self.assertEqual(state["rag_retrieval_count"],4)
                    task=MultipartTask(task_id="task-1",restaurant_id=N,restaurant_name="Natalina",criterion="cancellation_policy")
                    record,_=multipart.policy_record(task,passages(self.manifest,N,"policy"),self.manifest)
                    self.assertIn(workflow.safe_markdown(record[1]),result.text);self.assertEqual(state["rag_followup_resolution"]["item"],"margherita")
                if question==D4:
                    self.assertIn("not contain enough evidence",result.text);self.assertFalse(result.citations)
                    self.assertNotIn("no valet",result.text.lower())
            self.assertEqual(len(moderated),len(turns))
        selector.assert_not_called()
        self.assertLessEqual(ledger["maximum"],2)
        if not block_comparison:
            planner.ainvoke.assert_awaited_once()
            abstain.ainvoke.assert_awaited_once()
            self.assertEqual(len(ledger["calls"]),7) # D2 two, D3 four, D4 one fresh retrieval
            self.assertEqual(saved.call_count,4)


if __name__=="__main__":
    unittest.main()
