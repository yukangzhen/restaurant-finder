import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.application.document_rag import retrieval, workflow, comparison_workflow, multipart_workflow
from src.config import Settings, settings
from src.domain.document_rag import DocumentQuery, EvidenceIntegrityError, RetrievedEvidence
from src.evaluation import document_retrieval as e
from src.evaluation.rag_offline import SimulatedEmbeddings


class HybridRetrievalTests(unittest.TestCase):
    def test_mode_and_budget_validation_without_providers(self):
        self.assertEqual(Settings(_env_file=None).RAG_RETRIEVAL_MODE, "vector")
        self.assertEqual(Settings(_env_file=None, RAG_RETRIEVAL_MODE="vector", RAG_TOP_K=10).RAG_TOP_K, 10)
        for value in ("HYBRID", " hybrid", "hybrid\n", "", True, False, 1, [], {}):
            with self.subTest(mode=value):
                with self.assertRaises(ValueError): Settings(_env_file=None, RAG_RETRIEVAL_MODE=value)
                with self.assertRaises(ValueError): retrieval.DocumentRetriever(None,None,None,retrieval_mode=value)
        for value in (True, False, 0, 6, 1.0, "5", None):
            with self.assertRaises(ValueError):
                retrieval.DocumentRetriever(None,None,None,retrieval_mode="hybrid",top_k=value)
        for value in (True, 6, 1.0):
            with self.assertRaises(ValueError):
                Settings(_env_file=None, RAG_RETRIEVAL_MODE="hybrid", RAG_TOP_K=value)
        for value in (True, 0, -1, 9001, "9000"):
            with self.assertRaises(ValueError):
                retrieval.DocumentRetriever(None,None,None,retrieval_mode="hybrid",max_characters=value)

    def test_factories_pass_mode_and_keep_sessions_owned(self):
        import boto3
        sessions = [object(), object()]
        with e.offline_boundary(), patch.object(settings,"RAG_RETRIEVAL_MODE","hybrid"), \
             patch.object(workflow,"DocumentStore"), patch.object(workflow,"VectorStore"), patch.object(workflow,"TitanEmbeddings"):
            single = workflow.make_retriever()
        self.assertEqual(single.retrieval_mode,"hybrid")
        with e.offline_boundary(), patch.object(settings,"RAG_RETRIEVAL_MODE","hybrid"), \
             patch.object(boto3.session,"Session",side_effect=sessions), \
             patch("src.infrastructure.document_store.DocumentStore") as stores, \
             patch("src.infrastructure.vector_store.VectorStore"), patch("src.infrastructure.embeddings.TitanEmbeddings"):
            first,second = comparison_workflow.make_scoped_retriever(), comparison_workflow.make_scoped_retriever()
        self.assertEqual([first.retrieval_mode,second.retrieval_mode],["hybrid","hybrid"])
        self.assertEqual([call.kwargs["session"] for call in stores.call_args_list],sessions)
        self.assertIs(multipart_workflow.make_scoped_retriever,comparison_workflow.make_scoped_retriever)

    def test_keyword_only_distance_is_absent_and_vector_distance_is_observed(self):
        with e.offline_boundary():
            obs = e.run_retrieval(e.Simulation(question="mushroom",hits=[]))
        evidence = obs["evidence"][0]
        self.assertIsNone(evidence.distance)
        for value in (True,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                RetrievedEvidence.model_validate({**evidence.model_dump(),"distance":value})
        self.assertEqual(RetrievedEvidence.model_validate({**evidence.model_dump(),"distance":0}).distance,0.0)
        from src.domain.document_rag import DocumentCitation
        self.assertNotIn("distance",DocumentCitation.model_fields)

    def test_vector_order_and_options_are_preserved(self):
        manifest,refs=e.fixture()
        store=e.ObservedStore(manifest)
        vectors=SimpleNamespace(query=Mock(return_value=[
            {"key":manifest.generation_id+":"+refs[name].chunk_id,"distance":distance,"metadata":{
                "generation_id":manifest.generation_id,"chunk_id":refs[name].chunk_id,
                "restaurant_id":e.H,"document_id":refs[name].document_id,"document_type":"menu"}}
            for name,distance in [("soup",.9),("pasta",.1)]]))
        retriever=retrieval.DocumentRetriever(store,vectors,SimulatedEmbeddings(manifest.config))
        with e.offline_boundary():
            evidence=retriever.retrieve(DocumentQuery(query="mushroom",restaurant_id=e.H,document_type="menu"),manifest)
        self.assertEqual([item.chunk_id for item in evidence],[refs["soup"].chunk_id,refs["pasta"].chunk_id])
        self.assertEqual(vectors.query.call_args.kwargs,{})

    def test_vector_ties_in_hybrid_use_ids_and_only_one_page(self):
        with e.offline_boundary():
            obs=e.run_retrieval(e.Simulation(question="zzzz",hits=[e.Hit(ref="soup"),e.Hit(ref="pasta")],reverse=True))
        diag=obs["diagnostics"][0]
        self.assertEqual(list(diag.vector_keys),sorted(diag.vector_keys))
        self.assertEqual(obs["scopes"][0]["max_pages"],1)

    def test_changed_manifest_and_model_are_rejected_before_embedding(self):
        manifest,refs=e.fixture()
        for bad in (manifest.model_copy(update={"generation_id":"f"*64}),
                    manifest.model_copy(update={"chunks":[refs["pasta"].model_copy(update={"text":"forged"})]})):
            embed=SimulatedEmbeddings(manifest.config)
            retriever=retrieval.DocumentRetriever(e.ObservedStore(manifest),None,embed,retrieval_mode="hybrid")
            with e.offline_boundary(),self.assertRaises(EvidenceIntegrityError):
                retriever.retrieve(DocumentQuery(query="mushroom",restaurant_id=e.H),bad)
            self.assertEqual(embed.attempts,0)

    def test_unknown_scope_and_clarification_do_no_embedding(self):
        manifest,_=e.fixture()
        embed=SimulatedEmbeddings(manifest.config)
        retriever=retrieval.DocumentRetriever(e.ObservedStore(manifest),None,embed,retrieval_mode="hybrid")
        for query in (DocumentQuery(query="mushroom",restaurant_id="unknown"),
                      DocumentQuery(query="mushroom",restaurant_id=e.H,clarification="Choose a restaurant")):
            with e.offline_boundary(),self.assertRaises(ValueError): retriever.retrieve(query,manifest)
        self.assertEqual(embed.attempts,0)

    def test_expired_guard_never_starts_another_operation(self):
        for fault, counts in [("expired",(0,0,0)),("keyword",(0,0,0)),("embedding_expiry",(1,0,0)),
                              ("vector_expiry",(1,1,0)),("read_expiry",(1,1,1)),("cancelled",(0,0,0))]:
            with self.subTest(fault=fault),e.offline_boundary():
                obs=e.run_retrieval(e.Simulation(fault=fault,hits=[e.Hit(ref="pasta")]))
            self.assertEqual(obs["error_type"],"TimeoutError")
            self.assertEqual((obs["embedding"],obs["retrieval"],len(obs["reads"])),counts)

    def test_keyword_source_failure_never_degrades_to_vector_success(self):
        with e.offline_boundary():
            obs=e.run_retrieval(e.Simulation(corrupt_ref="pasta",hits=[e.Hit(ref="soup")]))
        self.assertEqual(obs["error_type"],"EvidenceIntegrityError")
        self.assertEqual(obs["evidence"],[])

    def test_budget_keeps_records_and_does_not_backfill(self):
        manifest,refs=e.fixture("wide")
        with e.offline_boundary():
            obs=e.run_retrieval(e.Simulation(fixture="wide",question="lexicalneedle",max_characters=50))
        self.assertEqual(obs["evidence"],[])
        self.assertEqual(len(obs["reads"]),5)
        self.assertTrue(all(len(c.text)>50 for c in manifest.chunks))
        # Two rank-1 candidates consume the top-two slots. The long one cannot
        # fit; a third short candidate must not be substituted from lower ranks.
        from src.application.document_rag.ingestion import prepare_generation
        with TemporaryDirectory(prefix="retrieval-budget-") as temp:
            root=Path(temp)
            (root/"menu.md").write_text("## Long\n\n"+"needle "*30+
                "\n\n## ShortA\n\nRice.\n\n## ShortB\n\nSoup.\n",encoding="utf-8")
            corpus={"fictional":True,"restaurants":retrieval.router_catalog(),"documents":[{
                "document_id":"budget-menu","restaurant_id":e.H,"document_type":"menu","version":"v1","path":"menu.md"}]}
            (root/"corpus.json").write_text(json.dumps(corpus),encoding="utf-8")
            manifest,_=prepare_generation(root/"corpus.json")
        refs={c.section:c for c in manifest.chunks}
        def hits(*args,**kwargs):
            return [{"key":manifest.generation_id+":"+refs[name].chunk_id,"distance":distance,"metadata":{
                "generation_id":manifest.generation_id,"chunk_id":refs[name].chunk_id,"document_id":"budget-menu",
                "restaurant_id":e.H,"document_type":"menu"}} for name,distance in (("ShortA",.1),("ShortB",.2))]
        retriever=retrieval.DocumentRetriever(e.ObservedStore(manifest),SimpleNamespace(query=hits),
            SimulatedEmbeddings(manifest.config),retrieval_mode="hybrid",top_k=2,max_characters=50)
        with e.offline_boundary():
            evidence=retriever.retrieve(DocumentQuery(query="needle",restaurant_id=e.H,document_type="menu"),manifest)
        self.assertEqual([c.chunk_id for c in evidence],[refs["ShortA"].chunk_id])

    def test_observer_failure_cannot_return_evidence(self):
        manifest,_=e.fixture()
        embed=SimulatedEmbeddings(manifest.config)
        store=e.ObservedStore(manifest)
        vectors=SimpleNamespace(query=lambda *a,**k:[])
        observer=Mock(side_effect=RuntimeError("private observer body"))
        retriever=retrieval.DocumentRetriever(store,vectors,embed,retrieval_mode="hybrid",diagnostics_observer=observer)
        with e.offline_boundary(),self.assertRaises(RuntimeError):
            retriever.retrieve(DocumentQuery(query="mushroom",restaurant_id=e.H,document_type="menu"),manifest)
        observer.assert_called_once()

    def test_new_spans_contain_counts_without_query_or_passages(self):
        observed=[]
        class Span:
            def set_attribute(self,key,value): observed.append((key,value))
        class Telemetry:
            @contextmanager
            def create_span(self,name,attributes=None):
                observed.append((name,attributes)); yield Span()
        with e.offline_boundary(),patch("src.infrastructure.rag_observability.get_observability_manager",return_value=Telemetry()):
            obs=e.run_retrieval(e.Simulation(hits=[e.Hit(ref="soup")]))
        rendered=json.dumps(observed)
        for name in ("rag.keyword_rank","rag.fuse","rag.candidate_union","bm25-rrf-v1"):
            self.assertIn(name,rendered)
        for value in ("mushroom","RM32",* [c.chunk_id for c in obs["manifest"].chunks]):
            self.assertNotIn(value,rendered)

    def test_offline_boundary_blocks_clients_and_http(self):
        import requests, socket
        with self.assertRaises(AssertionError):
            with e.offline_boundary(): requests.get("https://example.invalid")
        with self.assertRaises(AssertionError):
            with e.offline_boundary(): socket.create_connection(("example.invalid",443))
