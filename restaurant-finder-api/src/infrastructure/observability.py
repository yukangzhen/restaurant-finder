"""
Observability configuration for AgentCore.

Provides OpenTelemetry-based observability with CloudWatch integration for:
- Distributed tracing across agent workflows
- Session ID propagation for conversation tracking
- Custom span creation for detailed monitoring
- CloudWatch GenAI Observability dashboard integration

This module works with the AWS Distro for OpenTelemetry (ADOT) SDK which
automatically instruments the agent to capture telemetry data.

Environment Variables Required:
    AGENT_OBSERVABILITY_ENABLED: Enable observability (default: false)
    OTEL_PYTHON_DISTRO: Set to "aws_distro" for ADOT
    OTEL_PYTHON_CONFIGURATOR: Set to "aws_configurator" for ADOT
    OTEL_EXPORTER_OTLP_PROTOCOL: Set to "http/protobuf"
    OTEL_RESOURCE_ATTRIBUTES: Service name and resource attributes
    OTEL_EXPORTER_OTLP_LOGS_HEADERS: CloudWatch log group configuration

Usage:
    Run with automatic instrumentation:
        opentelemetry-instrument python -m src.main
"""

from typing import Optional
from contextlib import contextmanager
import time

from loguru import logger

# OpenTelemetry imports - gracefully handle if not installed
try:
    from opentelemetry import _logs, metrics, trace, baggage
    from opentelemetry.context import attach, detach
    from opentelemetry._logs import LogRecord, SeverityNumber
    from opentelemetry.trace import SpanKind, Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # Define stub types to prevent NameError at class definition time
    _logs = None  # type: ignore
    metrics = None  # type: ignore
    trace = None  # type: ignore
    baggage = None  # type: ignore
    context = None  # type: ignore
    attach = None  # type: ignore
    detach = None  # type: ignore
    SpanKind = None  # type: ignore
    Status = None  # type: ignore
    StatusCode = None  # type: ignore
    LogRecord = None  # type: ignore
    SeverityNumber = None  # type: ignore
    logger.warning(
        "OpenTelemetry packages not installed. "
        "Observability features will be disabled."
    )


class ObservabilityManager:
    """
    Manages OpenTelemetry observability for the AgentCore application.

    Provides utilities for:
    - Session ID propagation via OpenTelemetry baggage
    - Custom span creation for workflow steps
    - Trace context management
    """

    def __init__(
        self,
        service_name: str = "restaurant-finder-agent",
        enabled: bool = True,
    ):
        """
        Initialize the observability manager.

        Args:
            service_name: Name of the service for tracing attribution
            enabled: Whether observability is enabled
        """
        self.service_name = service_name
        self.enabled = enabled and OTEL_AVAILABLE
        self._tracer = None  # Type: Optional[trace.Tracer] when OTEL available
        self._memory_save_counter = None
        self._memory_retrieve_counter = None
        self._memory_duration = None
        self._otel_logger = None

        if self.enabled and trace is not None:
            self._tracer = trace.get_tracer(
                instrumenting_module_name=service_name,
                tracer_provider=trace.get_tracer_provider(),
            )
            meter = metrics.get_meter(service_name) if metrics is not None else None
            if meter is not None:
                self._memory_save_counter = meter.create_counter(
                    "agentcore.memory.save.count", unit="{event}"
                )
                self._memory_retrieve_counter = meter.create_counter(
                    "agentcore.memory.retrieve.count", unit="{operation}"
                )
                self._memory_duration = meter.create_histogram(
                    "agentcore.memory.operation.duration", unit="ms"
                )
            if _logs is not None:
                self._otel_logger = _logs.get_logger(service_name)
            logger.info(
                "OpenTelemetry instrumentation initialized; export delivery is not verified at startup"
            )
        else:
            logger.info("Observability disabled or OpenTelemetry not available")

    def set_session_id(self, session_id: str) -> Optional[object]:
        """
        Set session ID in OpenTelemetry baggage for trace correlation.

        Session IDs enable grouping of traces across multiple requests
        in the same conversation, viewable in CloudWatch GenAI Observability.

        Args:
            session_id: Unique session/conversation identifier

        Returns:
            Context token for detaching, or None if disabled
        """
        if not self.enabled or baggage is None or attach is None:
            return None

        try:
            ctx = baggage.set_baggage("session.id", session_id)
            token = attach(ctx)
            logger.debug("Session ID attached to observability context")
            return token
        except Exception as e:
            logger.warning(f"Failed to set session ID in baggage: {e}")
            return None

    def clear_session_context(self, token: object) -> None:
        """
        Clear the session context from OpenTelemetry baggage.

        Args:
            token: Context token from set_session_id
        """
        if not self.enabled or token is None or detach is None:
            return

        try:
            detach(token)
            logger.debug("Session context cleared from observability")
        except Exception as e:
            logger.warning(f"Failed to clear session context: {e}")

    @contextmanager
    def session_context(self, session_id: str):
        """
        Context manager for session-scoped observability.

        Automatically sets and clears session ID in OpenTelemetry baggage.

        Args:
            session_id: Unique session/conversation identifier

        Usage:
            with observability.session_context("conversation-123"):
                # All traces within this block will be tagged with session ID
                result = await process_request(...)
        """
        token = self.set_session_id(session_id)
        try:
            yield
        finally:
            self.clear_session_context(token)

    @contextmanager
    def create_span(
        self,
        name: str,
        kind=None,
        attributes: Optional[dict] = None,
    ):
        """
        Create a custom span for detailed workflow tracing.

        Use this to add custom instrumentation for specific operations
        like tool invocations, LLM calls, or business logic steps.

        Args:
            name: Name of the span (e.g., "orchestrator.tool_selection")
            kind: Type of span (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
            attributes: Custom attributes to attach to the span

        Usage:
            with observability.create_span("memory_retrieval", attributes={"actor_id": "user-123"}):
                memories = await memory.retrieve(...)
        """
        if not self.enabled or self._tracer is None:
            # Yield a no-op context when disabled
            yield None
            return

        # Default to INTERNAL span kind when not specified
        if kind is None and SpanKind is not None:
            kind = SpanKind.INTERNAL

        with self._tracer.start_as_current_span(
            name=name,
            kind=kind,
            attributes=attributes or {},
        ) as span:
            try:
                yield span
            except Exception as error:
                # Exception messages can contain request data or provider details.
                span.set_attribute("error.type", type(error).__name__)
                span.set_status(Status(StatusCode.ERROR))
                raise

    def add_span_attribute(self, key: str, value: str) -> None:
        """
        Add an attribute to the current span.

        Args:
            key: Attribute key
            value: Attribute value
        """
        if not self.enabled or trace is None:
            return

        try:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute(key, value)
        except Exception as e:
            logger.warning(f"Failed to add span attribute: {e}")

    def add_span_event(self, name: str, attributes: Optional[dict] = None) -> None:
        """
        Add an event to the current span.

        Events represent discrete occurrences within a span, useful for
        logging tool invocations, LLM responses, or state transitions.

        Args:
            name: Event name (e.g., "tool_invoked", "llm_response_received")
            attributes: Event attributes
        """
        if not self.enabled or trace is None:
            return

        try:
            current_span = trace.get_current_span()
            if current_span:
                current_span.add_event(name, attributes=attributes or {})
        except Exception as e:
            logger.warning(f"Failed to add span event: {e}")

    def record_workflow_step(
        self,
        step_name: str,
        step_type: str,
        duration_ms: Optional[float] = None,
        success: bool = True,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Record a workflow step as a span event with standard attributes.

        Args:
            step_name: Name of the workflow step (e.g., "orchestrator", "memory_post_hook")
            step_type: Type of step (e.g., "node", "edge", "tool")
            duration_ms: Duration of the step in milliseconds
            success: Whether the step succeeded
            metadata: Additional metadata to record
        """
        attributes = {
            "workflow.step.name": step_name,
            "workflow.step.type": step_type,
            "workflow.step.success": success,
        }

        if duration_ms is not None:
            attributes["workflow.step.duration_ms"] = duration_ms

        if metadata:
            for key, value in metadata.items():
                # Prefix custom metadata to avoid conflicts
                attributes[f"workflow.step.{key}"] = str(value)

        self.add_span_event(f"workflow.{step_name}", attributes)

    def record_memory_operation(
        self,
        operation: str,
        success: bool,
        duration_ms: float,
        category: str | None = None,
    ) -> None:
        """Record bounded-cardinality memory metrics and a sanitized OTel log."""
        if operation not in {"save", "retrieve"}:
            return

        status = "success" if success else "error"
        attributes = {"operation": operation, "status": status}
        if category in {"preferences", "facts", "summaries"}:
            attributes["category"] = category

        counter = (
            self._memory_save_counter
            if operation == "save"
            else self._memory_retrieve_counter
        )
        if counter is not None:
            counter.add(1, attributes)
        if self._memory_duration is not None:
            self._memory_duration.record(duration_ms, attributes)

        if self._otel_logger is not None and LogRecord is not None:
            severity = SeverityNumber.INFO if success else SeverityNumber.ERROR
            self._otel_logger.emit(
                LogRecord(
                    timestamp=time.time_ns(),
                    observed_timestamp=time.time_ns(),
                    severity_number=severity,
                    severity_text="INFO" if success else "ERROR",
                    body=f"memory.{operation}",
                    attributes=attributes,
                )
            )


# Global observability manager instance
_observability_manager: Optional[ObservabilityManager] = None


def get_observability_manager() -> ObservabilityManager:
    """
    Get the global observability manager instance.

    Returns:
        ObservabilityManager singleton instance
    """
    global _observability_manager

    if _observability_manager is None:
        from src.config import settings

        _observability_manager = ObservabilityManager(
            service_name=settings.OTEL_SERVICE_NAME,
            enabled=settings.AGENT_OBSERVABILITY_ENABLED,
        )

    return _observability_manager


def initialize_observability(
    service_name: str = "restaurant-finder-agent",
    enabled: bool = True,
) -> ObservabilityManager:
    """
    Initialize the global observability manager.

    Call this at application startup to configure observability.

    Args:
        service_name: Name of the service for tracing
        enabled: Whether observability is enabled

    Returns:
        Initialized ObservabilityManager instance
    """
    global _observability_manager

    _observability_manager = ObservabilityManager(
        service_name=service_name,
        enabled=enabled,
    )

    return _observability_manager
