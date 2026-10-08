import copy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from src.application.document_rag.ingestion import prepare_generation, publish_generation
from src.domain.document_rag import ActivePointer, DocumentSpec, RagConfig, validate_vector
from src.infrastructure.document_parser import chunk_document, extract_units, load_corpus
from src.infrastructure.document_store import DocumentStore
from src.infrastructure.embeddings import TitanEmbeddings
from src.infrastructure.vector_store import VectorStore

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "sample_documents" / "corpus.json"


class FakeStore:
    def __init__(self):
        self.data, self.pointer, self.etag = {}, None, None
        self.conflict = False
    def active(self, key="rag/active.json"):
        return self.pointer, self.etag
    def read_json(self, key, optional=False):
        if key not in self.data and not optional:
            raise ValueError("Missing stored object")
        return copy.deepcopy(self.data.get(key)), "etag"
    def write_json(self, key, value):
        self.data[key] = copy.deepcopy(value)
    def write_bytes(self, key, value, content_type):
        self.data[key] = value
    def publish_pointer(self, pointer, etag, key="rag/active.json"):
        if self.conflict or etag != self.etag:
            raise ClientError({"Error": {"Code": "PreconditionFailed"}}, "PutObject")
        self.pointer, self.etag = pointer, "new-etag"


class FakeEmbeddings:
    config = RagConfig()
    def __init__(self):
        self.attempts, self.tokens = 0, 0
    def embed(self, text):
        self.attempts += 1
        return [1.0] + [0.0] * 511


class FakeVectors:
    def __init__(self):
        self.data, self.put_attempts, self.query_calls = {}, 0, []
        self.fail_put = False
    def validate_index(self):
        pass
    def put(self, records):
        self.put_attempts += 1
        if self.fail_put:
            raise RuntimeError("Partial staging failure")
        self.data.update({r["key"]: copy.deepcopy(r) for r in records})
    def get(self, keys):
        return [copy.deepcopy(self.data[k]) for k in keys if k in self.data]
    def query(self, vector, generation_id, restaurant_id, document_type=None, top_k=5):
        self.query_calls.append((generation_id, restaurant_id, document_type))
        return [{"key": r["key"], "metadata": r["metadata"], "distance": 0.1} for r in self.data.values()
                if r["metadata"]["generation_id"] == generation_id and r["metadata"]["restaurant_id"] == restaurant_id
                and (not document_type or r["metadata"]["document_type"] == document_type)][:top_k]


class ParserTests(unittest.TestCase):
    def test_dry_run_has_zero_aws_clients_and_stable_generation(self):
        with patch("boto3.client", side_effect=AssertionError), patch("boto3.Session", side_effect=AssertionError):
            first, _ = prepare_generation(CORPUS)
            second, _ = prepare_generation(CORPUS)
        self.assertEqual(first, second)
        self.assertEqual(len(first.sources), 6)
        self.assertLessEqual(len(first.chunks), 48)
        pdf = next(c for c in first.chunks if c.document_id == "harbor-menu")
        self.assertEqual(pdf.page, 1)
        self.assertIn("Mushroom pasta - RM28 per serving. Contains wheat and milk.", pdf.text)
        self.assertTrue(all(c.page or (c.section and c.line_start) for c in first.chunks))

    def test_chunk_keeps_rows_and_respects_limit_overlap_scope(self):
        spec = DocumentSpec(document_id="demo-menu", restaurant_id="demo-harbor-pasta", path="menu.md", document_type="menu", version="v1")
        rows = [f"Dish {i} - RM28 per serving. Contains milk. " + "x"*90 for i in range(30)]
        chunks = chunk_document(spec, ("# Menu\n\n" + "\n\n".join(rows) + "\n\n# Policy\n\nNo refunds.").encode())
        self.assertTrue(all(len(c.text) <= 1800 for c in chunks))
        for row in rows:
            self.assertTrue(any(row in c.text for c in chunks))
        self.assertFalse(any("Dish" in c.text and "No refunds" in c.text for c in chunks))
        with self.assertRaisesRegex(ValueError, "Indivisible"):
            chunk_document(spec, ("# Menu\n\n"+"a"*1801).encode())

    def test_empty_and_unsupported_rejected(self):
        for source, suffix in [(b"", ".md"), (b"plain", ".txt")]:
            with self.assertRaises(ValueError):
                extract_units(source, suffix)

    def test_traversal_and_duplicate_catalog_rejected(self):
        with TemporaryDirectory() as temp:
            path = Path(temp)/"corpus.json"
            data = json.loads(CORPUS.read_text())
            data["documents"][0]["path"] = "../outside.pdf"
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_corpus(path)
            data["documents"][0]["path"] = "C:/outside.pdf"
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_corpus(path)
            data["documents"].append(data["documents"][0])
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_corpus(path)

    def test_vectors_reject_wrong_dimension_nonfinite_zero_and_boolean(self):
        for value in [[1.0]*511, [float("nan")]*512, [0.0]*512, [True]*512]:
            with self.assertRaises(ValueError):
                validate_vector(value)

    def test_pdf_empty_page_page_limit_and_currency_preserved(self):
        from pypdf import PdfWriter
        stream = io.BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=200,height=200)
        writer.write(stream)
        with self.assertRaisesRegex(ValueError,"no extractable text"):
            extract_units(stream.getvalue(),".pdf")
        for _ in range(10):
            writer.add_blank_page(width=200,height=200)
        stream = io.BytesIO()
        writer.write(stream)
        with self.assertRaisesRegex(ValueError,"1 to 10 pages"):
            extract_units(stream.getvalue(),".pdf")
        unit=extract_units("# Policy\n\nNo refunds. Price is RM28.50; not RM28.".encode(),".md")[0]
        self.assertIn("RM28.50",unit.text)
        self.assertIn("not RM28",unit.text)


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.manifest, self.sources = prepare_generation(CORPUS)
        self.store, self.vectors, self.embeddings = FakeStore(), FakeVectors(), FakeEmbeddings()
    def publish(self, manifest=None, sources=None):
        return publish_generation(manifest or self.manifest, sources or self.sources, self.store, self.vectors, self.embeddings, sleep=lambda _: None)
    def test_publish_then_identical_no_new_embeddings_or_vector_writes(self):
        first = self.publish()
        attempts = self.embeddings.attempts
        second = self.publish()
        self.assertEqual(first["status"], "published")
        self.assertEqual(second["status"], "unchanged")
        self.assertEqual(second["embeddings"], 0)
        self.assertEqual(self.embeddings.attempts, attempts)
        self.assertEqual(self.vectors.put_attempts, 1)
    def test_failed_staging_keeps_old_pointer(self):
        self.publish()
        old = self.store.pointer
        self.vectors.fail_put = True
        manifest, sources = self.updated()
        with self.assertRaises(RuntimeError):
            self.publish(manifest, sources)
        self.assertEqual(self.store.pointer, old)
    def test_concurrent_conflict_does_not_overwrite(self):
        self.store.conflict = True
        with self.assertRaisesRegex(RuntimeError, "conflict"):
            self.publish()
        self.assertIsNone(self.store.pointer)
    def test_update_reuses_unchanged_embeddings_and_retains_old_generation(self):
        self.publish()
        old = self.store.pointer.generation_id
        manifest, sources = self.updated()
        result = self.publish(manifest, sources)
        self.assertNotEqual(old, manifest.generation_id)
        self.assertEqual(result["embeddings"], 1)
        self.assertEqual(result["cache_hits"], len(manifest.chunks)-1)
        self.assertTrue(any(k.startswith(old+":") for k in self.vectors.data))
        self.assertEqual(self.store.pointer.generation_id, manifest.generation_id)
    def test_readiness_failure_never_publishes(self):
        self.vectors.query = Mock(return_value=[])
        with self.assertRaisesRegex(RuntimeError, "readiness"):
            self.publish()
        self.assertIsNone(self.store.pointer)
        self.assertLessEqual(self.vectors.query.call_count, 10)
    def test_invalid_cache_rejected_before_vector_write(self):
        from src.application.document_rag.ingestion import cache_key
        key = cache_key(self.manifest.chunks[0].text, self.manifest.config)
        self.store.data[key] = {"fingerprint": key.rsplit("/",1)[1].removesuffix(".json"), "vector": [1.0]}
        with self.assertRaises(ValueError):
            self.publish()
        self.assertEqual(self.vectors.put_attempts, 0)

    def test_rollback_verified_generation_uses_cas_without_embeddings(self):
        from src.application.document_rag.ingestion import rollback_generation
        self.publish()
        old = self.store.pointer.generation_id
        manifest,sources = self.updated()
        self.publish(manifest,sources)
        attempts = self.embeddings.attempts
        result=rollback_generation(old,self.store,self.vectors,self.embeddings)
        self.assertEqual(result["status"],"rolled_back")
        self.assertEqual(self.store.pointer.generation_id,old)
        self.assertEqual(self.embeddings.attempts,attempts)
    def updated(self):
        # Prepare a real corpus variant using checked-in text PDF fixture; preserve source containment.
        data = json.loads(CORPUS.read_text())
        data["documents"][0].update(path="harbor-menu-v2.pdf", version="v2")
        with TemporaryDirectory(dir=CORPUS.parent) as temp:
            folder = Path(temp)
            for spec in data["documents"]:
                (folder/spec["path"]).write_bytes((CORPUS.parent/spec["path"]).read_bytes())
            path = folder/"corpus.json"
            path.write_text(json.dumps(data))
            return prepare_generation(path)


class AdapterTests(unittest.TestCase):
    def test_pointer_conditional_write_parameters(self):
        client = Mock()
        store = DocumentStore("corpus", "us-east-2", client=client)
        pointer = ActivePointer(generation_id="a"*64, manifest_key="rag/generations/"+"a"*64+"/manifest.json")
        store.publish_pointer(pointer, None)
        self.assertEqual(client.put_object.call_args.kwargs["IfNoneMatch"], "*")
        store.publish_pointer(pointer, '"etag"')
        self.assertEqual(client.put_object.call_args.kwargs["IfMatch"], '"etag"')
    def test_titan_parameters_token_count_and_attempt_budget(self):
        client = Mock()
        client.invoke_model.return_value = {"body": io.BytesIO(json.dumps({"embedding": [1.0]+[0.0]*511, "inputTextTokenCount": 4}).encode())}
        adapter = TitanEmbeddings("us-east-2", client=client, max_attempts=1)
        self.assertEqual(len(adapter.embed("hello")), 512)
        params = client.invoke_model.call_args.kwargs
        self.assertEqual(json.loads(params["body"]), {"inputText":"hello","dimensions":512,"normalize":True,"embeddingTypes":["float"]})
        self.assertEqual(adapter.tokens, 4)
        with self.assertRaisesRegex(RuntimeError, "budget"):
            adapter.embed("again")
    def test_installed_service_models_accept_required_fields(self):
        import boto3
        from botocore.stub import Stubber
        client = boto3.client("s3vectors", region_name="us-east-2", aws_access_key_id="fixture", aws_secret_access_key="fixture")
        adapter = VectorStore("arn:aws:s3vectors:us-east-2:123456789012:bucket/demo/index/documents", "us-east-2", client=client)
        with Stubber(client) as stub:
            stub.add_response("query_vectors", {"vectors": [], "distanceMetric":"cosine"}, {"indexArn":adapter.index_arn,"topK":5,
                "queryVector":{"float32":[1.0]+[0.0]*511},"filter":{"$and":[{"generation_id":{"$eq":"g"}},{"restaurant_id":{"$eq":"r"}},{"document_type":{"$eq":"menu"}}]},
                "returnDistance":True,"returnMetadata":True})
            self.assertEqual(adapter.query([1.0]+[0.0]*511, "g", "r", "menu"), [])


if __name__ == "__main__":
    unittest.main()
