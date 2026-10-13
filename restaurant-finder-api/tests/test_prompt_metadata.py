import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.infrastructure.prompt_metadata import get_prompt_metadata


class PromptMetadataTests(unittest.TestCase):
    def test_nine_prompt_manifest_revalidates_cached_objects_and_new_prompt(self):
        from src.domain import prompts
        from src.infrastructure.prompt_manager import Prompt
        from src.infrastructure.prompt_metadata import validate_prompt_manifest
        objects = [value for value in vars(prompts).values() if isinstance(value, Prompt)]
        self.assertEqual(len(objects), 9)
        entries = {p.name: {"name": p.name, "id": "id", "arn": f"arn:aws:bedrock:us-east-2:123456789012:prompt/{p.name}:1",
                           "version": "1", "content_hash": hashlib.sha256(p.prompt.encode()).hexdigest()} for p in objects}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"manifest.json"
            with patch.dict(os.environ, {"PROMPT_MANIFEST_PATH": str(path), "REQUIRE_PROMPT_MANIFEST": "true", "PROMPT_SYNC_MODE": "false"}):
                path.write_text(json.dumps({"schemaVersion": 1, "prompts": entries}), encoding="utf-8")
                result = validate_prompt_manifest()
                self.assertEqual(result["prompt_count"], 9)
                self.assertIn("RAG_MULTIPART_PLAN_PROMPT", result["prompts"])
                missing = {k: v for k, v in entries.items() if k != "RAG_MULTIPART_PLAN_PROMPT"}
                path.write_text(json.dumps({"schemaVersion": 1, "prompts": missing}), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "missing"):
                    validate_prompt_manifest()
                entries["RAG_MULTIPART_PLAN_PROMPT"]["content_hash"] = "wrong"
                path.write_text(json.dumps({"schemaVersion": 1, "prompts": entries}), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "differs"):
                    validate_prompt_manifest()

    def test_manifest_returns_pinned_metadata_after_hash_validation(self):
        prompt_text = "Hello {{customer_name}}"
        prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "prompt-manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "prompts": {
                            "HELLO": {
                                "id": "prompt-id",
                                "arn": "arn:aws:bedrock:us-east-2:123456789012:prompt/prompt-id:1",
                                "version": "1",
                                "name": "HELLO",
                                "variables": ["customer_name"],
                                "content_hash": prompt_hash,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"PROMPT_MANIFEST_PATH": str(path), "REQUIRE_PROMPT_MANIFEST": "true"},
            ):
                metadata = get_prompt_metadata("HELLO", prompt_text)

        self.assertEqual(metadata["version"], "1")
        self.assertEqual(metadata["variables"], ["customer_name"])

    def test_manifest_rejects_a_prompt_text_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "prompt-manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "prompts": {
                            "HELLO": {
                                "id": "prompt-id",
                                "arn": "arn:aws:bedrock:us-east-2:123456789012:prompt/prompt-id:1",
                                "version": "1",
                                "name": "HELLO",
                                "content_hash": "wrong",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"PROMPT_MANIFEST_PATH": str(path), "REQUIRE_PROMPT_MANIFEST": "true"},
            ):
                with self.assertRaisesRegex(RuntimeError, "differs"):
                    get_prompt_metadata("HELLO", "changed")


if __name__ == "__main__":
    unittest.main()
