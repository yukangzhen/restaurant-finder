import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.infrastructure.prompt_metadata import get_prompt_metadata


class PromptMetadataTests(unittest.TestCase):
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
