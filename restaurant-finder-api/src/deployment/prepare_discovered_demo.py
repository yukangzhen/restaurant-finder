"""Prepare reviewed discovery-source additions locally, without providers.

Run python -m src.deployment.prepare_discovered_demo --base-corpus PATH
    --research PATH --output PATH

research/reviewed.json contains the base generation ID and two reviewed DocumentSpec
objects, each accompanied by its local currency-evidence filename. Acquisition,
PDF rendering, embeddings and publication are deliberately separate operations.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path

from src.application.document_rag.ingestion import prepare_generation
from src.application.document_rag.native_menu import registered_records
from src.domain.document_rag import CorpusSpec, DocumentSpec, RetrievedEvidence, canonical_text, digest
from src.infrastructure.document_parser import extract_units, load_corpus


class _HtmlSourceText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def _local_file(root, name):
    if not isinstance(name, str) or Path(name).name != name or "\\" in name or ":" in name:
        raise ValueError("Reviewed inputs must be plain local filenames")
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Reviewed input is missing or exceeds its source bound")
    return path


def _currency_text(path):
    data = path.read_bytes()
    if path.suffix.lower() == ".pdf":
        return canonical_text(" ".join(unit.text for unit in extract_units(data, ".pdf")))
    if path.suffix.lower() == ".html":
        parser = _HtmlSourceText()
        parser.feed(data.decode("utf-8"))
        return canonical_text(" ".join(parser.parts))
    raise ValueError("Currency evidence must be the retained official PDF or HTML")


def prepare(base_corpus: Path, research: Path, output: Path):
    base_corpus, research, output = base_corpus.resolve(), research.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Use a new output directory; never overwrite a prepared generation")
    if output.is_relative_to(research) or research.is_relative_to(output) or output.is_relative_to(base_corpus.parent):
        raise ValueError("Prepared output must be separate from retained input directories")
    review = json.loads((research / "reviewed.json").read_text(encoding="utf-8"))
    base, originals = load_corpus(base_corpus)
    retained, _ = prepare_generation(base_corpus)
    if retained.generation_id != review["base_generation_id"]:
        raise ValueError("Base generation differs from reviewed immutable sources")
    entries = review["documents"]
    if len(entries) != 2:
        raise ValueError("This preparation admits exactly two reviewed menu additions")
    documents = [DocumentSpec.model_validate(entry["document"]) for entry in entries]
    expected_ids = {"demo-ciccio-kl", "demo-bottega-kl"}
    if {d.restaurant_id for d in documents} != expected_ids or any(d.document_type != "menu" for d in documents):
        raise ValueError("Only the two reviewed discovered-restaurant menus are admitted")
    catalog = json.loads((Path(__file__).resolve().parents[1] / "domain/real_restaurant_catalog.json").read_text(encoding="utf-8"))
    by_id = {entry["restaurant_id"]: entry for entry in catalog["restaurants"]}
    if not expected_ids <= by_id.keys():
        raise ValueError("Reviewed venues are absent from the trusted router catalog")
    if expected_ids & {r.restaurant_id for r in base.restaurants}:
        raise ValueError("New venues must not replace an existing source scope")
    candidate = CorpusSpec(schema_version=2, fictional=False,
                          restaurants=[*base.restaurants, *(by_id[rid] for rid in sorted(expected_ids))],
                          documents=[*base.documents, *documents])
    source_bytes = {d.path: originals[d.document_id] for d in base.documents}
    proof_receipts = []
    for entry, document in zip(entries, documents):
        if document.native_menu is None or document.provenance is None:
            raise ValueError("New menus require reviewed row and provenance metadata")
        data = _local_file(research, document.path).read_bytes()
        if digest(data) != document.provenance.content_sha256:
            raise ValueError("Reviewed original bytes differ from the source hash")
        if document.path in source_bytes:
            raise ValueError("New document filename collides with a retained source")
        proof = _local_file(research, entry["currency_evidence"])
        profile = document.native_menu
        if (profile.currency != "MYR" or digest(proof.read_bytes()) != profile.currency_source_sha256
                or canonical_text(profile.currency_excerpt) not in _currency_text(proof)):
            raise ValueError("Reviewed currency proof differs from retained source evidence")
        source_bytes[document.path] = data
        proof_receipts.append({"document_id": document.document_id, "source_hash": digest(data),
                               "currency_evidence_hash": profile.currency_source_sha256})
    if any(Path(name).name != name or "\\" in name or ":" in name for name in source_bytes):
        raise ValueError("Prepared sources must have plain local filenames")
    # Reviewed provenance/hashes are checked first; extraction/chunk and native
    # row validation follows against the newly written, never-overwritten copy.
    output.mkdir(parents=True)
    for name, data in source_bytes.items():
        target = output / name
        target.write_bytes(data)
    spec_path = output / "corpus.json"
    spec_path.write_text(candidate.model_dump_json(indent=2) + "\n", encoding="utf-8")
    manifest, prepared_originals = prepare_generation(spec_path)
    rows = []
    for rid in sorted(expected_ids):
        venue = next(r for r in manifest.restaurants if r.restaurant_id == rid)
        evidence = [RetrievedEvidence(**c.model_dump(exclude={"key"}), generation_id=manifest.generation_id,
                                      restaurant_name=venue.name) for c in manifest.chunks if c.restaurant_id == rid]
        found = registered_records("Margherita", rid, evidence, manifest)
        if len(found) != 1:
            raise ValueError("Complete reviewed Margherita row did not survive extraction/chunking")
        row = found[0]
        rows.append({"restaurant_id": rid, "amount": str(row.amount), "currency": row.currency,
                     "unit": "listed_item", "page": row.evidence.page, "quote": row.quote,
                     "charge_note": row.charge_note})
    old_texts = {c.text for c in retained.chunks}
    report = {"status": "prepared_offline", "generation_id": manifest.generation_id,
              "retained_generation_id": retained.generation_id, "documents": len(prepared_originals),
              "restaurants": len(manifest.restaurants), "chunks": len(manifest.chunks),
              "chunks_by_document": dict(Counter(c.document_id for c in manifest.chunks)),
              "new_chunk_texts_vs_base": len({c.text for c in manifest.chunks if c.text not in old_texts}),
              "maximum_embeddings_without_cache": len(manifest.chunks),
              "native_records": rows, "source_proofs": proof_receipts,
              "aws_calls": 0, "application_sends": 0, "published": False}
    (output / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-corpus", type=Path, required=True)
    parser.add_argument("--research", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.base_corpus, args.research, args.output), indent=2))
