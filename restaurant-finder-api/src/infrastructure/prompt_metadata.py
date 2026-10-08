"""Read-only loading and validation of the deployment-generated prompt manifest."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def default_manifest_path() -> Path:
    configured = os.environ.get("PROMPT_MANIFEST_PATH")
    if configured:
        return Path(configured)
    api_root = Path(__file__).resolve().parents[2]
    return api_root / ".generated" / "prompt-manifest.json"


def _load_manifest() -> dict[str, Any] | None:
    if os.environ.get("PROMPT_SYNC_MODE", "").lower() in {"1", "true", "yes"}:
        return None

    path = default_manifest_path()
    if not path.exists():
        if os.environ.get("REQUIRE_PROMPT_MANIFEST", "false").lower() in {"1", "true", "yes"}:
            raise RuntimeError(
                f"Required Bedrock prompt manifest is missing: {path}. "
                "Run `python -m src.deployment.sync_prompts` before packaging."
            )
        return None

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Unable to read Bedrock prompt manifest: {path}") from error
    if manifest.get("schemaVersion") != 1 or not isinstance(manifest.get("prompts"), dict):
        raise RuntimeError(f"Unsupported Bedrock prompt manifest format: {path}")
    return manifest


def get_prompt_metadata(name: str, prompt_text: str) -> dict[str, Any] | None:
    """Return pinned prompt metadata and ensure it describes the local text."""
    manifest = _load_manifest()
    if manifest is None:
        return None
    entry = manifest["prompts"].get(name)
    if entry is None:
        raise RuntimeError(f"Prompt {name!r} is missing from the deployment manifest.")
    expected_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
    if entry.get("content_hash") != expected_hash:
        raise RuntimeError(
            f"Prompt {name!r} differs from the Bedrock version recorded in the manifest. "
            "Run the prompt sync command and package the generated manifest."
        )
    if not all(entry.get(key) for key in ("id", "arn", "version", "name")):
        raise RuntimeError(f"Prompt {name!r} has incomplete immutable version metadata.")
    return {
        "id": entry["id"],
        "arn": entry["arn"],
        "version": str(entry["version"]),
        "name": entry["name"],
        "variables": entry.get("variables", []),
    }


def validate_prompt_manifest() -> dict[str, Any]:
    """Validate all eight local prompts against the manifest without AWS calls."""
    manifest = _load_manifest()
    if manifest is None:
        raise RuntimeError("No Bedrock prompt manifest is available to validate.")

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

    prompt_objects = (
        RAG_QUERY_PROMPT,
        RAG_ANSWER_PROMPT,
        SEARCH_AGENT_PROMPT,
        RESTAURANT_EXPLORER_PROMPT,
        ROUTER_PROMPT,
        SIMPLE_RESPONSE_PROMPT,
        RESTAURANT_EXTRACTION_PROMPT,
        RESEARCH_EXTRACTION_PROMPT,
    )
    return {
        "manifest": str(default_manifest_path()),
        "prompt_count": len(prompt_objects),
        "prompts": {
            prompt.name: prompt.bedrock_metadata["arn"]
            for prompt in prompt_objects
            if prompt.bedrock_metadata is not None
        },
    }
