"""Synchronize local prompts to Bedrock and atomically write a version manifest.

Run from ``restaurant-finder-api`` with:
    python -m src.deployment.sync_prompts [--profile default] [--region us-east-2]

This command makes Bedrock Prompt Management writes. It is intentionally
separate from application startup and request processing.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="AWS CLI profile; defaults to the SDK credential chain")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-2"))
    parser.add_argument("--manifest", help="Override output manifest path")
    return parser.parse_args()


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.",
            suffix=".tmp", delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main() -> int:
    args = _arguments()
    os.environ["PROMPT_SYNC_MODE"] = "true"
    os.environ["AWS_REGION"] = args.region
    if args.manifest:
        os.environ["PROMPT_MANIFEST_PATH"] = args.manifest

    import boto3

    from src.infrastructure.prompt_manager import PromptManager
    from src.infrastructure.prompt_metadata import default_manifest_path
    from src.domain.prompts import (
        RAG_QUERY_PROMPT,
        RAG_ANSWER_PROMPT,
        RESEARCH_EXTRACTION_PROMPT,
        RESTAURANT_EXPLORER_PROMPT,
        RESTAURANT_EXTRACTION_PROMPT,
        ROUTER_PROMPT,
        SEARCH_AGENT_PROMPT,
        SIMPLE_RESPONSE_PROMPT,
    )

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    sts = session.client("sts")
    account_id = sts.get_caller_identity()["Account"]
    manager = PromptManager(bedrock_client=session.client("bedrock-agent"))

    prompts = (
        RAG_QUERY_PROMPT,
        RAG_ANSWER_PROMPT,
        SEARCH_AGENT_PROMPT,
        RESTAURANT_EXPLORER_PROMPT,
        ROUTER_PROMPT,
        SIMPLE_RESPONSE_PROMPT,
        RESTAURANT_EXTRACTION_PROMPT,
        RESEARCH_EXTRACTION_PROMPT,
    )
    entries: dict[str, dict[str, Any]] = {}
    for prompt in prompts:
        metadata = manager.get_or_create_prompt(
            name=prompt.name,
            prompt_text=prompt.prompt,
            description=f"Restaurant Finder {prompt.name.replace('_', ' ').lower()} prompt",
        )
        entries[prompt.name] = metadata

    manifest = {
        "schemaVersion": 1,
        "awsAccountId": account_id,
        "awsRegion": args.region,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "prompts": entries,
    }
    destination = Path(args.manifest) if args.manifest else default_manifest_path()
    _write_manifest(destination, manifest)
    print(f"Wrote immutable metadata for {len(entries)} prompts to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
