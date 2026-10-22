"""Offline dry-run by default; --publish explicitly stages and activates a corpus."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from src.application.document_rag.ingestion import prepare_generation, publish_generation, rollback_generation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("sample_documents/corpus.json"))
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Explicit offline mode (also the default)")
    parser.add_argument("--rollback-generation", help="With --publish, reactivate a verified retained generation")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--region", default="us-east-2", choices=["us-east-2"])
    parser.add_argument("--bucket")
    parser.add_argument("--index-arn")
    parser.add_argument("--max-embedding-attempts", type=int, default=48)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.dry_run and args.publish:
        parser.error("Choose either --dry-run or --publish")
    if args.rollback_generation and not args.publish:
        parser.error("Rollback requires --publish; offline dry-run never calls AWS")
    manifest, sources = prepare_generation(args.corpus)
    result = {"status": "dry_run", "generation_id": manifest.generation_id, "documents": len(manifest.sources),
              "chunks": len(manifest.chunks), "maximum_embedding_attempts": len(manifest.chunks), "aws_calls": 0,
              "characters": sum(len(c.text) for c in manifest.chunks)}
    if args.publish:
        if not args.bucket or not args.index_arn or not 1 <= args.max_embedding_attempts <= 128:
            parser.error("Publication requires --bucket, --index-arn and an attempt budget from 1 to 128")
        print(json.dumps({**result, "status":"planned_publication", "embedding_attempt_cap":args.max_embedding_attempts,
                          "maximum_put_vectors_attempts":1, "maximum_vectors":len(manifest.chunks)}))
        import boto3
        from src.infrastructure.document_store import DocumentStore
        from src.infrastructure.embeddings import TitanEmbeddings
        from src.infrastructure.vector_store import VectorStore
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        from src.infrastructure.document_store import CLIENT_CONFIG
        identity = session.client("sts", config=CLIENT_CONFIG).get_caller_identity()
        expected_prefix = f"arn:aws:s3vectors:{args.region}:{identity['Account']}:bucket/"
        if not args.index_arn.startswith(expected_prefix):
            parser.error("Index region/account does not match the selected AWS identity")
        store = DocumentStore(args.bucket, args.region, session=session)
        vectors = VectorStore(args.index_arn, args.region, session=session)
        embeddings = TitanEmbeddings(args.region, session=session, max_attempts=args.max_embedding_attempts)
        try:
            result = (rollback_generation(args.rollback_generation, store, vectors, embeddings) if args.rollback_generation
                      else publish_generation(manifest, sources, store, vectors, embeddings))
            result["aws_account"] = identity["Account"]
        except Exception as error:
            result = {"status":"failed", "generation_id":manifest.generation_id, "error_type":type(error).__name__}
        finally:
            result.update({"embedding_attempts": embeddings.attempts, "embedding_tokens": embeddings.tokens, "put_vectors_attempts": vectors.put_attempts})
            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
