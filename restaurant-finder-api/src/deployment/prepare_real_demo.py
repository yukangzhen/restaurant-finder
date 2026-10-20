"""Prepare reviewed local originals without network access or corpus publication.

Run: python -m src.deployment.prepare_real_demo --research PATH --output PATH
The output contains third-party originals and must stay outside Git publication.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from src.application.document_rag.ingestion import prepare_generation
from src.application.document_rag.native_menu import registered_records
from src.domain.document_rag import RetrievedEvidence, digest

ROOT = Path(__file__).resolve().parents[1]
PDF_HASHES = {
    "natalina-menu": "9dbf4d8e111c1eff5396bfeb5eb9202c4f6b6909af64a86f8b2b606d28290e01",
    "nero-menu": "47d768800d2b1ff884349c0de431ebf643c8b254b6fa055f1c2a620a7a7e2471",
}
HEADINGS = {"TIME SLOTS", "OPERATION HOURS", "TABLE HOLD", "DINING DURATION",
            "FULL VENUE BUYOUT/PRIVATE EVENT", "DEPOSITS & PAYMENTS", "CORKAGE CHARGES",
            "DIETARY & SPECIAL REQUESTS", "CELEBRATION CAKE", "GENERAL COMFORT POLICIES",
            "Cancelation Policy:", "How to Cancel or Amend:"}


def capture_time(path):
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def write_once(path, data):
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Prepared source already exists with different bytes: {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def booking_snapshot(raw, source_url, captured_at):
    # Only add headings/metadata; preserve all visible source words and conditions.
    body = "\n".join("## " + line.rstrip(":") if line in HEADINGS else line for line in raw.splitlines())
    return ("# Captured booking-page snapshot\n\n"
            f"Source URL: {source_url}\nCaptured at: {captured_at}\n\n"
            "This is a captured public booking-page dialog, not a restaurant-issued PDF. "
            "Headings are formatted for navigation; the visible wording below is preserved.\n\n"
            + body + "\n").encode("utf-8")


def prepare(research: Path, output: Path):
    research, output = research.resolve(), output.resolve()
    base = ROOT.parent / "sample_documents"
    real = json.loads((ROOT / "domain/real_restaurant_catalog.json").read_text(encoding="utf-8"))["restaurants"]
    # Owner-approved isolation: leave the six fixture sources and old generation
    # untouched, and prepare a separate four-source demo generation.
    corpus = dict(schema_version=2, fictional=False, restaurants=real, documents=[])
    metadata = {row["name"]: row for row in json.loads((research / "source-metadata.json").read_text(encoding="utf-8"))}
    ledger = []
    for venue, stem, booking, ordering, page, start, end, category, price_position, decorative, note in [
        (real[0], "natalina", "natalina", "natalinaathome", 6, "MARGHE RIT A", "QUATTRO FORMA GGI", "PIZZA", "after_description", [], "All prices subjected to 10% service charge & 6% SST."),
        (real[1], "nero", "neronerokualalumpur", "neronero", 9, "Margherita", "Focaccia al Rosmarino", "Traditional Pizza", "after_title", [2,4,6,8,10], "All prices subjected to 10% servi ce charge & 6% SST."),
    ]:
        doc_id = stem + "-menu"
        pdf_path = research / (doc_id + ".pdf")
        data = pdf_path.read_bytes()
        if digest(data) != PDF_HASHES[doc_id]:
            raise ValueError("Original PDF differs from the visually reviewed snapshot")
        meta = metadata[doc_id]
        if meta["sha256"] != digest(data):
            raise ValueError("Research source ledger differs from original bytes")
        write_once(output / pdf_path.name, data)
        currency_path = research / (ordering + "-currency.txt")
        currency_text = currency_path.read_text(encoding="utf-8")
        excerpt = re.search(r"\bRM\s*\d+(?:\.\d{2})?", currency_text)
        if excerpt is None:
            raise ValueError("Explicit currency evidence is missing")
        provenance = dict(kind="official_pdf", origin_url=meta["origin_url"], resolved_url=meta["resolved_url"],
                          website_url=venue["website"], captured_at=capture_time(pdf_path), content_sha256=digest(data))
        corpus["documents"].append(dict(document_id=doc_id, restaurant_id=venue["restaurant_id"], path=pdf_path.name,
            document_type="menu", version="captured-2026-10-20", provenance=provenance,
            native_menu=dict(records=[dict(item="Margherita", category=category, page=page, start=start, end=end,
                price_position=price_position, charge_note=note)], decorative_pages=decorative, currency="MYR",
                currency_source_url=f"https://{ordering}.oddle.me/en_MY", currency_source_sha256=digest(currency_path.read_bytes()),
                currency_excerpt=excerpt[0])))
        raw = research / (booking + "-booking-terms.txt")
        url = f"https://www.sevenrooms.com/explore/{booking}/reservations/create/search/"
        snapshot = booking_snapshot(raw.read_text(encoding="utf-8"), url, capture_time(raw))
        filename = stem + "-booking-snapshot.md"
        write_once(output / filename, snapshot)
        corpus["documents"].append(dict(document_id=stem+"-booking", restaurant_id=venue["restaurant_id"], path=filename,
            document_type="policy", version="captured-2026-10-20", provenance=dict(kind="booking_page_snapshot",
            origin_url=url, resolved_url=url, website_url=venue["website"], captured_at=capture_time(raw), content_sha256=digest(snapshot))))
        ledger.append(dict(restaurant_id=venue["restaurant_id"], currency_capture_sha256=digest(currency_path.read_bytes()),
            booking_raw_sha256=digest(raw.read_bytes()), snapshot_sha256=digest(snapshot)))
    write_once(output / "corpus.json", (json.dumps(corpus, indent=2, ensure_ascii=False)+"\n").encode("utf-8"))
    manifest, originals = prepare_generation(output / "corpus.json")
    rows = []
    for venue in manifest.restaurants:
        if venue.fictional:
            continue
        evidence = [RetrievedEvidence(**c.model_dump(exclude={"key"}), generation_id=manifest.generation_id,
                    restaurant_name=venue.name) for c in manifest.chunks if c.restaurant_id == venue.restaurant_id]
        found = registered_records("Margherita", venue.restaurant_id, evidence, manifest)
        if len(found) != 1:
            raise ValueError("Reviewed native item did not survive actual extraction/chunking")
        from src.application.document_rag.multipart import policy_record
        from src.domain.document_multipart import MultipartTask
        task = MultipartTask(task_id="task-1", restaurant_id=venue.restaurant_id, restaurant_name=venue.name, criterion="cancellation_policy")
        record, reason = policy_record(task, [e for e in evidence if e.document_type == "policy"], manifest)
        if record is None:
            raise ValueError(f"Booking snapshot is unsupported: {reason}")
        policy, quote = record
        if not all(part in quote for part in ("24 hours or more", "per person", "No-show", "Any change to a reservation date")):
            raise ValueError("Cancellation conditions are incomplete")
        rows.append(dict(restaurant=venue.name, amount=str(found[0].amount), currency=found[0].currency,
                         unit="listed_item", page=found[0].evidence.page, policy_characters=len(quote)))
    if any("valet" in c.text.casefold() for c in manifest.chunks if c.restaurant_id == real[0]["restaurant_id"]):
        raise ValueError("The planned unsupported question is answered by the corpus")
    legacy, _ = prepare_generation(base / "corpus-v2.json")
    report = dict(generation_id=manifest.generation_id, documents=len(originals), chunks=len(manifest.chunks),
                  maximum_embedding_attempts=len(manifest.chunks), aws_calls=0, application_sends=0,
                  legacy_generation_id=legacy.generation_id, native_records=rows, capture_ledger=ledger)
    write_once(output / "manifest.json", (manifest.model_dump_json(indent=2)+"\n").encode("utf-8"))
    write_once(output / "report.json", (json.dumps(report, indent=2)+"\n").encode("utf-8"))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.research, args.output), indent=2))
