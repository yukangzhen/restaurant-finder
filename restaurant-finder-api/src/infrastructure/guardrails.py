"""
Guardrail infrastructure for AWS Bedrock Guardrails.

Provides automatic creation or retrieval of guardrails on application startup,
with configurable content filtering policies for the restaurant finder agent.
"""

import re

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from loguru import logger

from src.config import settings


class GuardrailManager:
    """
    Manages Bedrock Guardrails lifecycle - creates or retrieves existing guardrails.

    Similar pattern to ShortTermMemory for consistency.
    """

    def __init__(self, guardrail_name: str | None = None):
        self.guardrail_name = guardrail_name or settings.BEDROCK_GUARDRAIL_NAME
        self._guardrail_id: str | None = None
        self._guardrail_version: str | None = None
        # Snapshot caller configuration once. Automatic setup may subsequently
        # populate settings with DRAFT, without changing this manager's mode.
        guardrail_id = settings.BEDROCK_GUARDRAIL_ID
        version = settings.BEDROCK_GUARDRAIL_VERSION
        self._configured_pair: tuple[str, str] | None = None
        if guardrail_id != "" or version != "DRAFT":
            if (
                not isinstance(guardrail_id, str)
                or re.fullmatch(r"[a-z0-9]{1,2048}", guardrail_id) is None
                or not isinstance(version, str)
                or re.fullmatch(r"[1-9][0-9]{0,7}", version) is None
            ):
                raise GuardrailUnavailableError("Guardrail initialization unavailable.")
            self._configured_pair = (guardrail_id, version)
        try:
            self._client = boto3.client(
                "bedrock",
                region_name=settings.AWS_REGION,
                config=Config(
                    connect_timeout=5,
                    read_timeout=15,
                    retries={"total_max_attempts": 1},
                ),
            )
        except Exception:
            raise GuardrailUnavailableError("Guardrail initialization unavailable.") from None

    @property
    def guardrail_id(self) -> str | None:
        """Get the guardrail ID (available after initialization)."""
        return self._guardrail_id

    @property
    def guardrail_version(self) -> str | None:
        """Get the guardrail version (available after initialization)."""
        return self._guardrail_version

    def _get_default_content_policy(self) -> dict:
        """
        Get default content filter policy for the restaurant finder.

        Configures filters for harmful content categories with appropriate
        strengths for a restaurant recommendation application.
        """
        return {
            "filtersConfig": [
                {
                    "type": "HATE",
                    "inputStrength": "HIGH",
                    "outputStrength": "HIGH",
                },
                {
                    "type": "INSULTS",
                    "inputStrength": "HIGH",
                    "outputStrength": "HIGH",
                },
                {
                    "type": "SEXUAL",
                    "inputStrength": "HIGH",
                    "outputStrength": "HIGH",
                },
                {
                    "type": "VIOLENCE",
                    "inputStrength": "MEDIUM",
                    "outputStrength": "MEDIUM",
                },
                {
                    "type": "MISCONDUCT",
                    "inputStrength": "HIGH",
                    "outputStrength": "HIGH",
                },
                {
                    "type": "PROMPT_ATTACK",
                    "inputStrength": "MEDIUM",  # HIGH causes too many false positives
                    "outputStrength": "NONE",
                },
            ]
        }

    def _get_default_topic_policy(self) -> dict:
        """
        Get default topic policy for the restaurant finder.

        Blocks topics that are not relevant to restaurant recommendations.

        Note: We intentionally don't include a broad "off-topic" topic filter
        as it tends to block legitimate queries. The model's system prompt
        handles staying on topic more gracefully.
        """
        return {
            "topicsConfig": [
                {
                    "name": "competitor-services",
                    "definition": "Using, recommending or comparing competing third-party delivery, review or booking platforms. Excludes restaurants' own menu/policy records and their document provenance.",
                    "examples": [
                        "Can you order from DoorDash instead?",
                        "Is UberEats better than this?",
                        "Compare this to Yelp",
                    ],
                    "type": "DENY",
                },
                {
                    "name": "illegal-activities",
                    "definition": "Any requests related to illegal activities, substances, or services.",
                    "examples": [
                        "Where can I buy drugs?",
                        "Find restaurants that serve illegal wildlife",
                    ],
                    "type": "DENY",
                },
            ]
        }

    def _get_default_sensitive_info_policy(self) -> dict:
        """
        Get default sensitive information policy.

        Masks PII in inputs and outputs for privacy protection.
        """
        return {
            "piiEntitiesConfig": [
                {"type": "EMAIL", "action": "ANONYMIZE"},
                {"type": "PHONE", "action": "ANONYMIZE"},
                {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
                {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"},
            ]
        }

    def _get_default_word_policy(self) -> dict:
        """
        Get default word filter policy.

        Blocks profanity and configures managed word lists.
        """
        return {
            "managedWordListsConfig": [
                {"type": "PROFANITY"},
            ]
        }

    def _find_existing_guardrail(self) -> dict | None:
        """
        Find an existing guardrail by name.

        Returns:
            Guardrail details if found, None otherwise.
        """
        try:
            paginator = self._client.get_paginator("list_guardrails")
            for page in paginator.paginate():
                for guardrail in page.get("guardrails", []):
                    if guardrail.get("name") == self.guardrail_name:
                        logger.info(f"Found existing guardrail: {guardrail['id']}")
                        return guardrail
        except ClientError as e:
            logger.warning(f"Error listing guardrails: {e}")
        return None

    def _create_guardrail(self) -> dict:
        """
        Create a new guardrail with default policies.

        Returns:
            Created guardrail details.
        """
        logger.info(f"Creating new guardrail: {self.guardrail_name}")

        response = self._client.create_guardrail(
            name=self.guardrail_name,
            description="Content guardrail for the Restaurant Finder AI agent. "
                        "Filters harmful content, blocks off-topic requests, "
                        "and protects user privacy.",
            contentPolicyConfig=self._get_default_content_policy(),
            topicPolicyConfig=self._get_default_topic_policy(),
            sensitiveInformationPolicyConfig=self._get_default_sensitive_info_policy(),
            wordPolicyConfig=self._get_default_word_policy(),
            blockedInputMessaging=(
                "I'm sorry, but I can't process that request. "
                "I'm here to help you find great restaurants! "
                "Please ask me about dining options, cuisines, or restaurant recommendations."
            ),
            blockedOutputsMessaging=(
                "I apologize, but I cannot provide that information. "
                "Let me help you find a wonderful restaurant instead!"
            ),
        )

        logger.info(
            f"Created guardrail: {response['guardrailId']} "
            f"(version: {response['version']})"
        )

        return {
            "id": response["guardrailId"],
            "version": response["version"],
            "arn": response["guardrailArn"],
        }

    def _resolve_configured_guardrail(self) -> dict:
        """Validate the exact immutable pair without automatic setup fallback."""
        guardrail_id, version = self._configured_pair
        try:
            response = self._client.get_guardrail(
                guardrailIdentifier=guardrail_id,
                guardrailVersion=version,
            )
            if (
                not isinstance(response, dict)
                or response.get("guardrailId") != guardrail_id
                or response.get("version") != version
                or response.get("status") != "READY"
            ):
                raise GuardrailUnavailableError("Guardrail initialization unavailable.")
        except Exception:
            # SDK/provider error text can contain request data or credentials.
            raise GuardrailUnavailableError("Guardrail initialization unavailable.") from None
        self._guardrail_id = guardrail_id
        self._guardrail_version = version
        return {"id": guardrail_id, "version": version}

    def create_or_get_guardrail(self) -> dict:
        """
        Validate a configured immutable pair, or deliberately create/get by name.

        Returns:
            Dictionary with guardrail id, version, and arn.
        """
        # Check if already initialized
        if self._guardrail_id:
            return {
                "id": self._guardrail_id,
                "version": self._guardrail_version,
            }

        if self._configured_pair is not None:
            return self._resolve_configured_guardrail()

        # Try to find existing guardrail
        existing = self._find_existing_guardrail()

        if existing:
            self._guardrail_id = existing["id"]
            self._guardrail_version = existing.get("version", "DRAFT")
            return {
                "id": self._guardrail_id,
                "version": self._guardrail_version,
            }

        # Create new guardrail
        created = self._create_guardrail()
        self._guardrail_id = created["id"]
        self._guardrail_version = created["version"]

        return {
            "id": self._guardrail_id,
            "version": self._guardrail_version,
        }

    def publish_version(self, description: str = "Production version") -> str:
        """
        Publish a new version of the guardrail (moves from DRAFT to numbered version).

        Args:
            description: Description for the new version.

        Returns:
            The new version number.
        """
        if self._configured_pair is not None:
            raise GuardrailUnavailableError("Configured guardrail versions are immutable.")
        if not self._guardrail_id:
            raise ValueError("Guardrail not initialized. Call create_or_get_guardrail first.")

        response = self._client.create_guardrail_version(
            guardrailIdentifier=self._guardrail_id,
            description=description,
        )

        new_version = response["version"]
        logger.info(f"Published guardrail version: {new_version}")

        self._guardrail_version = new_version
        return new_version

    def get_guardrail_config(self) -> dict | None:
        """
        Get the guardrail configuration for use with ChatBedrockConverse.

        Returns:
            Guardrail config dict or None if disabled/not initialized.
        """
        if not settings.GUARDRAIL_ENABLED:
            return None

        if not self._guardrail_id:
            return None

        return {
            "guardrailIdentifier": self._guardrail_id,
            "guardrailVersion": self._guardrail_version or "DRAFT",
        }


# Singleton instance for application-wide use
_guardrail_manager: GuardrailManager | None = None


def get_guardrail_manager() -> GuardrailManager:
    """Get or create the singleton GuardrailManager instance."""
    global _guardrail_manager
    if _guardrail_manager is None:
        _guardrail_manager = GuardrailManager()
    return _guardrail_manager


# =============================================================================
# Graph-Level Guardrail Functions (ApplyGuardrail API)
# =============================================================================

class GuardrailResult:
    """Result of a guardrail check."""

    def __init__(
        self,
        allowed: bool,
        output: str,
        action: str,
        assessments: list | None = None,
    ):
        self.allowed = allowed
        self.output = output
        self.action = action
        self.assessments = assessments or []

    @property
    def safe_summary(self) -> dict:
        """Return bounded telemetry; failures must never affect moderation."""
        try:
            return summarize_guardrail_assessments(self.assessments)
        except Exception:
            # Provider data and exception messages must not reach telemetry.
            return _empty_assessment_summary(unavailable=True)

    def __repr__(self) -> str:
        return f"GuardrailResult(allowed={self.allowed}, action={self.action})"


class GuardrailUnavailableError(RuntimeError):
    """An enabled guardrail could not be applied; request processing must stop."""


_CONTENT_TYPES = frozenset({"HATE", "INSULTS", "SEXUAL", "VIOLENCE", "MISCONDUCT", "PROMPT_ATTACK"})
_PII_TYPES = frozenset({
    "ADDRESS", "AGE", "AWS_ACCESS_KEY", "AWS_SECRET_KEY", "CA_HEALTH_NUMBER",
    "CA_SOCIAL_INSURANCE_NUMBER", "CREDIT_DEBIT_CARD_CVV", "CREDIT_DEBIT_CARD_EXPIRY",
    "CREDIT_DEBIT_CARD_NUMBER", "DRIVER_ID", "EMAIL", "INTERNATIONAL_BANK_ACCOUNT_NUMBER",
    "IP_ADDRESS", "LICENSE_PLATE", "MAC_ADDRESS", "NAME", "PASSWORD", "PHONE", "PIN",
    "SWIFT_CODE", "UK_NATIONAL_HEALTH_SERVICE_NUMBER", "UK_NATIONAL_INSURANCE_NUMBER",
    "UK_UNIQUE_TAXPAYER_REFERENCE_NUMBER", "URL", "USERNAME", "US_BANK_ACCOUNT_NUMBER",
    "US_BANK_ROUTING_NUMBER", "US_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER", "US_PASSPORT_NUMBER",
    "US_SOCIAL_SECURITY_NUMBER", "VEHICLE_IDENTIFICATION_NUMBER",
})
_TOPIC_CATEGORIES = {"competitor-services": "competitor_services", "illegal-activities": "illegal_activities"}
_ASSESSMENT_PATHS = (
    ("contentPolicy", "filters", "content"),
    ("topicPolicy", "topics", "topic"),
    ("wordPolicy", "customWords", "custom_word"),
    ("wordPolicy", "managedWordLists", "managed_word"),
    ("sensitiveInformationPolicy", "piiEntities", "pii"),
    ("sensitiveInformationPolicy", "regexes", "regex"),
)


def _safe_enum(value, allowed) -> str:
    return value if type(value) is str and len(value) <= 64 and value in allowed else "unknown"


def _empty_assessment_summary(*, unavailable=False) -> dict:
    return {
        "assessment_count": 0, "entry_count": 0,
        "detected_count": 0, "nondetected_count": 0, "unknown_detection_count": 0,
        "blocked_categories": [], "anonymized_types": [], "entries": [],
        "policy_counts": {kind: 0 for _, _, kind in _ASSESSMENT_PATHS},
        "other_policy_present": False,
        "summary_incomplete": unavailable, "summary_unavailable": unavailable,
    }


def summarize_guardrail_assessments(assessments) -> dict:
    """Extract only fixed enums/counts from at most 20 assessments/100 leaves.

    No recursion, raw matches, arbitrary topic/regex names or provider reasons.
    This describes assessments; it never decides whether an answer is allowed.
    """
    summary = _empty_assessment_summary()
    if type(assessments) is not list:
        return _empty_assessment_summary(unavailable=True)
    summary["summary_incomplete"] = len(assessments) > 20
    known_keys = {path[0] for path in _ASSESSMENT_PATHS} | {"invocationMetrics", "appliedGuardrailDetails"}
    blocked, anonymized = set(), set()
    for assessment in assessments[:20]:
        summary["assessment_count"] += 1
        if type(assessment) is not dict:
            summary["summary_incomplete"] = True
            continue
        for index, key in enumerate(assessment):
            if index == 32:
                summary["summary_incomplete"] = True
                break
            if key not in known_keys:
                summary["other_policy_present"] = True
                summary["summary_incomplete"] = True
        for policy_name, collection, kind in _ASSESSMENT_PATHS:
            policy = assessment.get(policy_name, {})
            if type(policy) is not dict:
                summary["summary_incomplete"] = True
                continue
            leaves = policy.get(collection, [])
            if type(leaves) is not list:
                summary["summary_incomplete"] = True
                continue
            remaining = 100 - summary["entry_count"]
            if len(leaves) > remaining:
                summary["summary_incomplete"] = True
            for leaf in leaves[:remaining]:
                summary["entry_count"] += 1
                if type(leaf) is not dict:
                    summary["summary_incomplete"] = True
                    continue
                allowed_actions = {"NONE", "BLOCKED", "ANONYMIZED"} if kind in {"pii", "regex"} else {"NONE", "BLOCKED"}
                action = _safe_enum(leaf.get("action"), allowed_actions)
                detected = leaf.get("detected")
                detection = "detected" if detected is True else "not_detected" if detected is False else "unknown"
                if "detected" in leaf and type(detected) is not bool:
                    summary["summary_incomplete"] = True
                confidence = "unknown"
                if kind == "content":
                    category = "content:" + _safe_enum(leaf.get("type"), _CONTENT_TYPES)
                    confidence = _safe_enum(leaf.get("confidence"), {"NONE", "LOW", "MEDIUM", "HIGH"})
                    if confidence == "unknown":
                        summary["summary_incomplete"] = True
                elif kind == "topic":
                    name = leaf.get("name")
                    category = "topic:" + (_TOPIC_CATEGORIES.get(name, "other_topic") if type(name) is str and len(name) <= 64 else "other_topic")
                elif kind == "pii":
                    pii_type = _safe_enum(leaf.get("type"), _PII_TYPES)
                    category = "pii:" + (pii_type if pii_type != "unknown" else "other_pii")
                elif kind == "managed_word":
                    category = "managed_word:" + _safe_enum(leaf.get("type"), {"PROFANITY"})
                else:
                    category = kind
                if action == "unknown" or category.endswith((":unknown", ":other_topic", ":other_pii")):
                    summary["summary_incomplete"] = True
                count_key = {"detected": "detected_count", "not_detected": "nondetected_count", "unknown": "unknown_detection_count"}[detection]
                summary[count_key] += 1
                summary["policy_counts"][kind] += 1
                summary["entries"].append({"kind": kind, "category": category, "action": action,
                                           "detection": detection, "confidence": confidence})
                # Optional detection is unknown when absent. Explicit False is
                # never reported as an active intervention, including in FULL.
                if detected is not False and action == "BLOCKED":
                    blocked.add(category)
                if detected is not False and action == "ANONYMIZED" and kind == "pii":
                    anonymized.add(category.removeprefix("pii:"))
    summary["blocked_categories"] = sorted(blocked)
    summary["anonymized_types"] = sorted(anonymized)
    return summary


def guardrail_span_attributes(result: GuardrailResult | None, original_text: str) -> dict:
    """Content-free attributes for an existing final-moderation span."""
    summary = result.safe_summary if result is not None else _empty_assessment_summary(unavailable=True)
    changed = result is not None and result.output != original_text
    decision = "unavailable" if result is None else "blocked" if not result.allowed else "anonymized" if changed else "approved"
    return {
        "guardrail.action": _safe_enum(result.action, {"NONE", "GUARDRAIL_INTERVENED"}) if result is not None else "unknown",
        "guardrail.decision": decision,
        "guardrail.blocked_categories": summary["blocked_categories"],
        "guardrail.anonymized_types": summary["anonymized_types"],
        "guardrail.detected_count": summary["detected_count"],
        "guardrail.nondetected_count": summary["nondetected_count"],
        "guardrail.unknown_detection_count": summary["unknown_detection_count"],
        "guardrail.summary_incomplete": summary["summary_incomplete"],
        "guardrail.summary_unavailable": summary["summary_unavailable"],
        "guardrail.other_policy_present": summary["other_policy_present"],
        "guardrail.output_changed": changed,
    }


def _assessment_actions(value) -> set[str]:
    actions: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "action" and isinstance(item, str):
                actions.add(item.upper())
            else:
                actions.update(_assessment_actions(item))
    elif isinstance(value, list):
        for item in value:
            actions.update(_assessment_actions(item))
    return actions


def _apply_guardrail(text: str, source: str) -> GuardrailResult:
    if not settings.GUARDRAIL_ENABLED:
        return GuardrailResult(allowed=True, output=text, action="NONE")

    try:
        manager = get_guardrail_manager()
        if not manager.guardrail_id:
            raise GuardrailUnavailableError("configured guardrail is unavailable")

        runtime_client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        response = runtime_client.apply_guardrail(
            guardrailIdentifier=manager.guardrail_id,
            guardrailVersion=manager.guardrail_version or "DRAFT",
            source=source,
            content=[{"text": {"text": text}}],
        )
        action = str(response.get("action", "NONE")).upper()
        outputs = response.get("outputs", [])
        assessments = response.get("assessments", [])
        has_output = bool(outputs) and all(
            isinstance(item, dict) and isinstance(item.get("text"), str)
            for item in outputs
        )
        output_text = "".join(item["text"] for item in outputs) if has_output else text
        assessment_actions = _assessment_actions(assessments)
        explicitly_blocked = "BLOCKED" in assessment_actions
        anonymized = "ANONYMIZED" in assessment_actions

        # ApplyGuardrail's top-level intervention includes both redaction and
        # blocking. Allow only an explicit anonymization assessment with the
        # returned transformed text; block all other interventions.
        allowed = not explicitly_blocked and (
            action == "NONE" or (action == "GUARDRAIL_INTERVENED" and anonymized and has_output)
        )
        if not allowed:
            output_text = text
            logger.info("Guardrail blocked {} content (action={})", source.lower(), _safe_enum(action, {"NONE", "GUARDRAIL_INTERVENED"}))
        elif anonymized:
            logger.info("Guardrail anonymized {} content", source.lower())

        return GuardrailResult(
            allowed=allowed,
            output=output_text,
            action=action,
            assessments=assessments if isinstance(assessments, list) else [],
        )
    except GuardrailUnavailableError:
        raise
    except Exception as error:
        logger.error(
            "Guardrail application failed for {} (error_type={})",
            source.lower(),
            type(error).__name__,
        )
        raise GuardrailUnavailableError("configured guardrail could not be applied") from error


def apply_input_guardrail(text: str) -> GuardrailResult:
    """Check input before routing, returning anonymized text when approved."""
    return _apply_guardrail(text, "INPUT")


def apply_output_guardrail(text: str) -> GuardrailResult:
    """Check the complete final answer before display or memory persistence."""
    return _apply_guardrail(text, "OUTPUT")


def get_blocked_input_message() -> str:
    """Get the default message to show when input is blocked."""
    return (
        "I'm sorry, but I can't process that request. "
        "I'm here to help you find great restaurants! "
        "Please ask me about dining options, cuisines, or restaurant recommendations."
    )


def get_blocked_output_message() -> str:
    """Get the default message to show when output is blocked."""
    return (
        "I apologize, but I cannot provide that information. "
        "Let me help you find a wonderful restaurant instead!"
    )
