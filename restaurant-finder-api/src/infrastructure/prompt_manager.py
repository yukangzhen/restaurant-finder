"""Explicit deployment-time synchronization for Bedrock managed prompts."""

from __future__ import annotations

import hashlib
import re
from typing import Any

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from src.config import settings


class Prompt:
    """Local prompt text with optional immutable Bedrock version metadata."""

    def __init__(self, name: str, prompt: str) -> None:
        self.name = name
        self.__prompt_text = prompt
        self.__variables = self._extract_variables(prompt)

        # Import lazily: prompt definitions are imported by the sync command too.
        from src.infrastructure.prompt_metadata import get_prompt_metadata

        self.__bedrock_metadata = get_prompt_metadata(name, prompt)

    @staticmethod
    def _extract_variables(prompt_text: str) -> list[str]:
        seen: set[str] = set()
        return [
            name
            for name in re.findall(r"\{\{(\w+)\}\}", prompt_text)
            if not (name in seen or seen.add(name))
        ]

    @property
    def prompt(self) -> str:
        return self.__prompt_text

    @property
    def variables(self) -> list[str]:
        return self.__variables

    @property
    def bedrock_metadata(self) -> dict[str, Any] | None:
        return self.__bedrock_metadata

    def format(self, **kwargs: Any) -> str:
        missing = set(self.__variables) - set(kwargs)
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        result = self.__prompt_text
        for name, value in kwargs.items():
            result = result.replace(f"{{{{{name}}}}}", str(value))
        return result

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return self.__str__()


class PromptManager:
    """Sync prompt definitions and publish immutable versions explicitly.

    This manager is used by a deployment command, never by application import
    or request handling. It deliberately does not delete old prompt versions.
    """

    def __init__(self, bedrock_client=None) -> None:
        self.bedrock_client = bedrock_client or boto3.client(
            "bedrock-agent", region_name=settings.AWS_REGION
        )

    @staticmethod
    def extract_variables(prompt_text: str) -> list[dict[str, str]]:
        seen: set[str] = set()
        names = [
            name
            for name in re.findall(r"\{\{(\w+)\}\}", prompt_text)
            if not (name in seen or seen.add(name))
        ]
        if "user_input" not in seen:
            names.append("user_input")
        return [{"name": name} for name in names]

    @staticmethod
    def content_hash(prompt_text: str) -> str:
        return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

    def get_or_create_prompt(
        self, name: str, prompt_text: str, description: str = ""
    ) -> dict[str, Any]:
        """Create or update the draft, then return a verified immutable version."""
        existing = self._find_prompt_by_name(name)
        if existing is None:
            response = self.bedrock_client.create_prompt(
                name=name,
                description=description or f"Prompt managed by deployment: {name}",
                variants=self._build_variants(prompt_text),
                defaultVariant="default",
            )
            prompt_id = response["id"]
            prompt_arn = response["arn"]
        else:
            prompt_id = existing["id"]
            prompt_arn = existing["arn"]

        for version in reversed(self._list_prompt_versions(prompt_id)):
            version_number = version["version"]
            current = self.bedrock_client.get_prompt(
                promptIdentifier=prompt_id,
                promptVersion=version_number,
            )
            if self._matches_definition(current, prompt_text):
                logger.info("Reusing immutable Bedrock prompt {} version {}", name, version_number)
                return self._metadata(current, prompt_text)

        draft = self.bedrock_client.get_prompt(promptIdentifier=prompt_id)
        if not self._matches_definition(draft, prompt_text):
            self.bedrock_client.update_prompt(
                promptIdentifier=prompt_id,
                name=name,
                description=description or f"Prompt managed by deployment: {name}",
                variants=self._build_variants(prompt_text),
                defaultVariant="default",
            )

        try:
            version_response = self.bedrock_client.create_prompt_version(
                promptIdentifier=prompt_id,
                description=f"Deployment sync {self.content_hash(prompt_text)[:12]}",
            )
        except ClientError as error:
            message = str(error)
            if "max-number-versions-per-prompt" in message:
                raise RuntimeError(
                    f"Bedrock prompt {name!r} reached its immutable-version limit. "
                    "No versions were deleted. Review the prompt history and AWS quota "
                    "before changing it."
                ) from error
            raise

        immutable = self.bedrock_client.get_prompt(
            promptIdentifier=prompt_id,
            promptVersion=version_response["version"],
        )
        if not self._matches_definition(immutable, prompt_text):
            raise RuntimeError(
                f"Bedrock prompt {name!r} version {version_response['version']} "
                "did not match the local definition after read-back."
            )
        immutable.setdefault("id", prompt_id)
        immutable.setdefault("arn", version_response.get("arn", prompt_arn))
        immutable.setdefault("name", name)
        logger.info("Created immutable Bedrock prompt {} version {}", name, immutable["version"])
        return self._metadata(immutable, prompt_text)

    def _build_variants(self, prompt_text: str) -> list[dict[str, Any]]:
        return [
            {
                "name": "default",
                "templateType": "CHAT",
                "templateConfiguration": {
                    "chat": {
                        "system": [{"text": prompt_text}],
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"text": "{{user_input}}"}],
                            }
                        ],
                        "inputVariables": self.extract_variables(prompt_text),
                    }
                },
            }
        ]

    def _matches_definition(self, prompt: dict[str, Any], prompt_text: str) -> bool:
        variants = prompt.get("variants", [])
        default_variant = prompt.get("defaultVariant", "default")
        variant = next((v for v in variants if v.get("name") == default_variant), None)
        if not variant or variant.get("templateType") != "CHAT":
            return False
        chat = variant.get("templateConfiguration", {}).get("chat", {})
        system = chat.get("system", [])
        messages = chat.get("messages", [])
        system_text = system[0].get("text") if system else None
        user_text = None
        user_role = None
        if messages:
            user_role = messages[0].get("role")
            content = messages[0].get("content", [])
            user_text = content[0].get("text") if content else None
        input_names = {item.get("name") for item in chat.get("inputVariables", [])}
        expected_names = {item["name"] for item in self.extract_variables(prompt_text)}
        return (
            system_text == prompt_text
            and user_role == "user"
            and user_text == "{{user_input}}"
            and input_names == expected_names
        )

    def _find_prompt_by_name(self, name: str) -> dict[str, Any] | None:
        paginator = self.bedrock_client.get_paginator("list_prompts")
        for page in paginator.paginate():
            for prompt in page.get("promptSummaries", []):
                if prompt.get("name") == name:
                    return prompt
        return None

    def _list_prompt_versions(self, prompt_id: str) -> list[dict[str, Any]]:
        """Use ListPrompts filtered by identifier; there is no versions paginator."""
        versions: list[dict[str, Any]] = []
        paginator = self.bedrock_client.get_paginator("list_prompts")
        for page in paginator.paginate(promptIdentifier=prompt_id):
            versions.extend(
                summary
                for summary in page.get("promptSummaries", [])
                if summary.get("version") not in (None, "DRAFT")
            )
        return sorted(versions, key=lambda item: int(item["version"]))

    def _metadata(self, prompt_response: dict[str, Any], prompt_text: str) -> dict[str, Any]:
        return {
            "id": prompt_response["id"],
            "arn": prompt_response["arn"],
            "version": str(prompt_response["version"]),
            "name": prompt_response["name"],
            "variables": [
                item["name"]
                for item in self.extract_variables(prompt_text)
                if item["name"] != "user_input"
            ],
            "content_hash": self.content_hash(prompt_text),
        }

    def get_prompt(self, name: str) -> dict[str, Any] | None:
        """Return the prompt summary by name without creating or modifying it."""
        return self._find_prompt_by_name(name)
