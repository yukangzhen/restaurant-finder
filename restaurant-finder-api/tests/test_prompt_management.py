import os
import unittest
from unittest.mock import patch

from src.infrastructure.prompt_manager import Prompt, PromptManager


class _Paginator:
    def __init__(self, client):
        self.client = client

    def paginate(self, **kwargs):
        if kwargs.get("promptIdentifier"):
            summaries = self.client.versions
        else:
            summaries = self.client.prompts
        yield {"promptSummaries": summaries}


class _FakeBedrockClient:
    def __init__(self):
        self.prompts = []
        self.versions = []
        self.current = None
        self.create_version_calls = 0
        self.update_calls = 0

    def get_paginator(self, name):
        if name != "list_prompts":
            raise AssertionError(f"Unexpected paginator: {name}")
        return _Paginator(self)

    def create_prompt(self, **kwargs):
        self.current = {
            "id": "prompt-id",
            "arn": "arn:aws:bedrock:us-east-2:123456789012:prompt/prompt-id",
            "name": kwargs["name"],
            "version": "DRAFT",
            "defaultVariant": kwargs["defaultVariant"],
            "variants": kwargs["variants"],
        }
        self.prompts = [{key: self.current[key] for key in ("id", "arn", "name", "version")}]
        return self.current

    def get_prompt(self, promptIdentifier, promptVersion=None):
        if promptVersion is None:
            return self.current.copy()
        return self.versions[0]["response"].copy()

    def update_prompt(self, **kwargs):
        self.update_calls += 1
        self.current.update(
            name=kwargs["name"],
            defaultVariant=kwargs["defaultVariant"],
            variants=kwargs["variants"],
        )
        return self.current

    def create_prompt_version(self, promptIdentifier, description):
        self.create_version_calls += 1
        response = self.current.copy()
        response["version"] = str(self.create_version_calls)
        response["arn"] = f"{self.current['arn']}:{response['version']}"
        self.versions = [
            {
                "version": response["version"],
                "arn": response["arn"],
                "response": response,
            }
        ]
        return {"version": response["version"], "arn": response["arn"]}


class PromptManagementTests(unittest.TestCase):
    def test_prompt_construction_does_not_call_aws(self):
        with patch.dict(os.environ, {"PROMPT_SYNC_MODE": "true"}, clear=False):
            with patch("boto3.client", side_effect=AssertionError("AWS call during import")):
                prompt = Prompt("TEST_PROMPT", "Hello {{customer_name}}")

        self.assertEqual(prompt.variables, ["customer_name"])
        self.assertIsNone(prompt.bedrock_metadata)

    def test_sync_creates_a_version_then_reuses_matching_immutable_version(self):
        client = _FakeBedrockClient()
        manager = PromptManager(bedrock_client=client)
        text = "Find restaurants for {{customer_name}}"

        first = manager.get_or_create_prompt("SEARCH", text)
        second = manager.get_or_create_prompt("SEARCH", text)

        self.assertEqual(first["version"], "1")
        self.assertEqual(first["arn"], second["arn"])
        self.assertEqual(client.create_version_calls, 1)
        self.assertEqual(client.update_calls, 0)
        self.assertEqual(first["variables"], ["customer_name"])


if __name__ == "__main__":
    unittest.main()
