"""Stage complete immutable generations; conditionally switch the pointer last."""
from __future__ import annotations

import time
from pathlib import Path
from botocore.exceptions import ClientError

from src.domain.document_rag import ActivePointer, ChunkReference, GenerationManifest, RagConfig, SourceReference, digest, validate_vector
from src.infrastructure.document_parser import chunk_document, load_corpus


def verify_chunks(manifest, store):
    for chunk in manifest.chunks:
        stored, _ = store.read_json(chunk.key)
        if stored != chunk.model_dump(exclude={"key"}):
            raise ValueError("Staged chunk/hash verification failed")


def prepare_generation(corpus_path: Path):
    """Pure local operation. Never constructs an AWS client."""
    corpus, source_bytes = load_corpus(corpus_path)
    config = RagConfig()
    chunks = [c for doc in corpus.documents for c in chunk_document(doc, source_bytes[doc.document_id])]
    if not 1 <= len(chunks) <= 48:
        raise ValueError("Generation must contain 1 to 48 chunks")
    sources = sorted([[d.document_id, d.restaurant_id, d.document_type, d.version, digest(source_bytes[d.document_id])] for d in corpus.documents])
    generation_id = digest({"config": config.model_dump(), "restaurants": [r.model_dump() for r in corpus.restaurants], "sources": sources})
    root = f"rag/generations/{generation_id}/"
    manifest = GenerationManifest(generation_id=generation_id, config=config, restaurants=corpus.restaurants,
        sources=[SourceReference(**d.model_dump(), source_hash=digest(source_bytes[d.document_id]), key=root+f"sources/{d.document_id}{Path(d.path).suffix.lower()}") for d in corpus.documents],
        chunks=[ChunkReference(**c.model_dump(), key=root+f"chunks/{c.chunk_id}.json") for c in chunks])
    return manifest, source_bytes


def cache_key(text: str, config: RagConfig):
    return "rag/embedding-cache/" + digest({"text": text, "model": config.model_id, "dimensions": config.dimensions, "normalize": config.normalize}) + ".json"


def publish_generation(manifest, source_bytes, store, vectors, embeddings, *, active_key="rag/active.json", sleep=time.sleep, clock=time.monotonic):
    active, etag = store.active(active_key)
    vectors.validate_index()
    if active and active.generation_id == manifest.generation_id:
        stored, _ = store.read_json(active.manifest_key)
        if GenerationManifest.model_validate(stored) != manifest:
            raise ValueError("Active manifest differs from local generation")
        existing = vectors.get([f"{manifest.generation_id}:{c.chunk_id}" for c in manifest.chunks])
        verify_vectors(manifest, existing)
        verify_chunks(manifest, store)
        return {"status": "unchanged", "generation_id": manifest.generation_id, "embeddings": 0, "vectors_written": 0, "cache_hits": 0}
    records, cache_hits, attempts_before = [], 0, embeddings.attempts
    for source in manifest.sources:
        store.write_bytes(source.key, source_bytes[source.document_id], "application/pdf" if source.path.endswith(".pdf") else "text/markdown")
    for chunk in manifest.chunks:
        key = cache_key(chunk.text, manifest.config)
        cached, _ = store.read_json(key, optional=True)
        if cached is not None:
            if cached.get("fingerprint") != key.rsplit("/", 1)[-1].removesuffix(".json"):
                raise ValueError("Embedding cache fingerprint mismatch")
            vector = validate_vector(cached["vector"])
            cache_hits += 1
        else:
            vector = embeddings.embed(chunk.text)
            store.write_json(key, {"fingerprint": key.rsplit("/", 1)[-1].removesuffix(".json"), "vector": vector})
        store.write_json(chunk.key, chunk.model_dump(exclude={"key"}))
        records.append({"key": f"{manifest.generation_id}:{chunk.chunk_id}", "data": {"float32": vector}, "metadata": {
            "generation_id": manifest.generation_id, "chunk_id": chunk.chunk_id, "document_id": chunk.document_id,
            "restaurant_id": chunk.restaurant_id, "document_type": chunk.document_type}})
    verify_chunks(manifest, store)
    vectors.put(records)  # <=48; one attempt, no hidden retry
    deadline = clock() + 60
    ready = False
    for poll in range(10):
        try:
            if clock() >= deadline:
                raise RuntimeError("Readiness deadline exhausted; active pointer unchanged")
            staged = vectors.get([r["key"] for r in records])
            verify_vectors(manifest, staged)
            if {r["key"]: validate_vector(r["data"]["float32"]) for r in staged} != {r["key"]: validate_vector(r["data"]["float32"]) for r in records}:
                raise ValueError("Staged embedding data differs from prepared vectors")
            # A self-query for every scope verifies filter/query readiness using stored embeddings.
            for scope in sorted({(c.restaurant_id, c.document_type) for c in manifest.chunks}):
                if clock() >= deadline:
                    raise RuntimeError("Readiness deadline exhausted; active pointer unchanged")
                record = next(r for r in records if (r["metadata"]["restaurant_id"], r["metadata"]["document_type"]) == scope)
                hits = vectors.query(record["data"]["float32"], manifest.generation_id, *scope)
                expected = {r["key"] for r in records if (r["metadata"]["restaurant_id"], r["metadata"]["document_type"]) == scope}
                if record["key"] not in {h["key"] for h in hits} or any(h["key"] not in expected for h in hits):
                    raise ValueError("Filtered query is not ready")
            ready = True
            break
        except (ValueError, ClientError):
            if poll == 9 or clock() >= deadline:
                raise RuntimeError("Generation readiness failed; active pointer unchanged")
            sleep(min(3, max(0, deadline-clock())))
    if not ready:
        raise RuntimeError("Generation not ready")
    manifest_key = f"rag/generations/{manifest.generation_id}/manifest.json"
    store.write_json(manifest_key, manifest.model_dump())
    stored, _ = store.read_json(manifest_key)
    if GenerationManifest.model_validate(stored) != manifest:
        raise ValueError("Manifest verification failed")
    pointer = ActivePointer(generation_id=manifest.generation_id, manifest_key=manifest_key)
    try:
        store.publish_pointer(pointer, etag, active_key)
    except ClientError as error:
        if error.response["Error"]["Code"] in {"PreconditionFailed", "ConditionalRequestConflict", "412", "409"}:
            current, _ = store.active(active_key)
            raise RuntimeError(f"Concurrent publication conflict; staged generation inactive; current={current.generation_id if current else 'none'}") from error
        raise
    return {"status": "published", "generation_id": manifest.generation_id, "previous_generation": active.generation_id if active else None,
            "embeddings": embeddings.attempts-attempts_before, "cache_hits": cache_hits, "vectors_written": len(records)}


def verify_vectors(manifest, records):
    expected = {f"{manifest.generation_id}:{c.chunk_id}": c for c in manifest.chunks}
    if len(records) != len(expected) or {r["key"] for r in records} != set(expected):
        raise ValueError("Staged vector set is incomplete")
    for record in records:
        chunk = expected[record["key"]]
        metadata = record["metadata"]
        if metadata != {"generation_id": manifest.generation_id, "chunk_id": chunk.chunk_id, "document_id": chunk.document_id,
                         "restaurant_id": chunk.restaurant_id, "document_type": chunk.document_type}:
            raise ValueError("Staged vector metadata mismatch")
        validate_vector(record["data"]["float32"])


def rollback_generation(generation_id, store, vectors, embeddings, *, active_key="rag/active.json"):
    """Explicitly reactivate a verified retained generation; never delete anything."""
    pointer = ActivePointer(generation_id=generation_id, manifest_key=f"rag/generations/{generation_id}/manifest.json")
    current, etag = store.active(active_key)
    data, _ = store.read_json(pointer.manifest_key)
    manifest = GenerationManifest.model_validate(data)
    if manifest.generation_id != generation_id or manifest.config != embeddings.config:
        raise ValueError("Retained generation is incompatible")
    vectors.validate_index()
    verify_chunks(manifest, store)
    records = vectors.get([f"{generation_id}:{c.chunk_id}" for c in manifest.chunks])
    verify_vectors(manifest, records)
    for record in records:
        metadata = record["metadata"]
        hits = vectors.query(record["data"]["float32"], generation_id, metadata["restaurant_id"], metadata["document_type"])
        if record["key"] not in {h["key"] for h in hits}:
            raise ValueError("Retained generation is not query-ready")
    store.publish_pointer(pointer, etag, active_key)
    return {"status":"rolled_back", "generation_id":generation_id, "previous_generation":current.generation_id if current else None,
            "embedding_attempts":0, "put_vectors_attempts":0}
