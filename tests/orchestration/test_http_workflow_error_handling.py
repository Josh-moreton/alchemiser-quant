"""Business Unit: orchestration | Status: current.

Unit tests for HTTP workflow error handling and retry logic.

Tests error scenarios including network failures, malformed responses,
missing configuration, and HTTP error codes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from dependency_injector import providers

from the_alchemiser.orchestration.event_driven_orchestrator import (
    EventDrivenOrchestrator,
)
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.shared.events import WorkflowStarted


class TestPostWithRetries:
    """Tests for _post_with_retries method."""

    def test_retries_on_http_error_and_eventually_raises(self) -> None:
        """Test that HTTP errors trigger retries and eventually raise."""
        container = ApplicationContainer.create_for_testing()
        custom_settings = Settings()
        custom_settings.orchestration.http_max_retries = 3
        container.config.settings.override(providers.Object(custom_settings))

        # Mock HTTP client that always fails
        def failing_transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "Internal Server Error"})

        http_client = httpx.Client(transport=httpx.MockTransport(failing_transport))
        orchestrator = EventDrivenOrchestrator(container, http_client=http_client)

        payload = {"event_id": "test-123", "correlation_id": "corr-123"}

        # Should retry 3 times and then raise
        with pytest.raises(httpx.HTTPStatusError):
            orchestrator._post_with_retries("http://test.local/endpoint", payload)

    def test_retries_on_timeout_and_eventually_raises(self) -> None:
        """Test that timeout errors trigger retries and eventually raise."""
        container = ApplicationContainer.create_for_testing()
        custom_settings = Settings()
        custom_settings.orchestration.http_max_retries = 2
        container.config.settings.override(providers.Object(custom_settings))

        # Mock HTTP client that times out
        def timeout_transport(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Request timed out")

        http_client = httpx.Client(transport=httpx.MockTransport(timeout_transport))
        orchestrator = EventDrivenOrchestrator(container, http_client=http_client)

        payload = {"event_id": "test-timeout", "correlation_id": "corr-timeout"}

        with pytest.raises(httpx.TimeoutException):
            orchestrator._post_with_retries("http://test.local/endpoint", payload)

    def test_succeeds_after_transient_failure(self) -> None:
        """Test that transient failures are retried and eventually succeed."""
        container = ApplicationContainer.create_for_testing()

        attempt_count = 0

        def flaky_transport(request: httpx.Request) -> httpx.Response:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                return httpx.Response(503, json={"error": "Service Unavailable"})
            return httpx.Response(200, json={"event": {"event_type": "SignalGenerated"}})

        http_client = httpx.Client(transport=httpx.MockTransport(flaky_transport))
        orchestrator = EventDrivenOrchestrator(container, http_client=http_client)

        payload = {"event_id": "test-flaky", "correlation_id": "corr-flaky"}
        result = orchestrator._post_with_retries("http://test.local/endpoint", payload)

        assert result == {"event": {"event_type": "SignalGenerated"}}
        assert attempt_count == 3  # Succeeded on third attempt

    def test_idempotency_guard_prevents_duplicate_requests(self) -> None:
        """Test that idempotency cache prevents duplicate HTTP calls."""
        container = ApplicationContainer.create_for_testing()

        call_count = 0

        def counting_transport(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json={"event": {"event_type": "SignalGenerated"}})

        http_client = httpx.Client(transport=httpx.MockTransport(counting_transport))
        orchestrator = EventDrivenOrchestrator(container, http_client=http_client)

        payload = {"event_id": "test-duplicate", "correlation_id": "corr-dup"}
        url = "http://test.local/endpoint"

        # First call should hit the endpoint
        result1 = orchestrator._post_with_retries(url, payload)
        assert call_count == 1

        # Second call with same event_id should be cached
        result2 = orchestrator._post_with_retries(url, payload)
        assert call_count == 1  # No additional call
        assert result2 == {}  # Returns empty dict for cached requests


class TestDeserializeEventFromPayload:
    """Tests for _deserialize_event_from_payload method."""

    def test_returns_none_for_non_dict_payload(self) -> None:
        """Test that non-dict payloads return None with error logging."""
        container = ApplicationContainer.create_for_testing()
        orchestrator = EventDrivenOrchestrator(container)

        result = orchestrator._deserialize_event_from_payload("not a dict")  # type: ignore[arg-type]
        assert result is None

    def test_returns_none_for_missing_event_type(self) -> None:
        """Test that payloads without event_type return None."""
        container = ApplicationContainer.create_for_testing()
        orchestrator = EventDrivenOrchestrator(container)

        payload = {"correlation_id": "test-123", "timestamp": "2024-01-01T00:00:00Z"}
        result = orchestrator._deserialize_event_from_payload(payload)
        assert result is None

    def test_returns_none_for_unknown_event_type(self) -> None:
        """Test that unknown event types return None with error logging."""
        container = ApplicationContainer.create_for_testing()
        orchestrator = EventDrivenOrchestrator(container)

        payload = {
            "event_type": "UnknownEventType",
            "correlation_id": "test-unknown",
            "causation_id": "cause-123",
            "event_id": "event-123",
            "timestamp": datetime.now(UTC),
            "source_module": "test",
            "source_component": "test",
        }
        result = orchestrator._deserialize_event_from_payload(payload)
        assert result is None

    def test_returns_none_for_validation_failure(self) -> None:
        """Test that Pydantic validation failures return None."""
        container = ApplicationContainer.create_for_testing()
        orchestrator = EventDrivenOrchestrator(container)

        # Missing required fields for SignalGenerated
        payload = {
            "event_type": "SignalGenerated",
            "correlation_id": "test-invalid",
            # Missing many required fields
        }
        result = orchestrator._deserialize_event_from_payload(payload)
        assert result is None

    def test_deserializes_wrapped_event_payload(self) -> None:
        """Test deserialization of payload with {"event": {...}} wrapper."""
        container = ApplicationContainer.create_for_testing()
        orchestrator = EventDrivenOrchestrator(container)

        payload: dict[str, Any] = {
            "event": {
                "event_type": "SignalGenerated",
                "correlation_id": "test-wrapped",
                "causation_id": "cause-123",
                "event_id": "event-123",
                "timestamp": datetime.now(UTC).isoformat(),
                "source_module": "strategy_v2",
                "source_component": "test",
                "signals_data": {"AAPL": {"weight": 0.3}},
                "consolidated_portfolio": {"AAPL": 0.2},
                "signal_count": 1,
                "metadata": {},
            }
        }

        result = orchestrator._deserialize_event_from_payload(payload)
        assert result is not None
        assert result.event_type == "SignalGenerated"


class TestEndpointConfiguration:
    """Tests for endpoint configuration validation."""

    def test_raises_error_when_strategy_endpoint_missing(self) -> None:
        """Test that missing strategy endpoint raises ConfigurationError."""
        container = ApplicationContainer.create_for_testing()
        custom_settings = Settings()
        custom_settings.orchestration.use_http_domain_workflow = True
        custom_settings.orchestration.strategy_endpoint = ""  # Not configured
        container.config.settings.override(providers.Object(custom_settings))

        orchestrator = EventDrivenOrchestrator(container)

        event = WorkflowStarted(
            correlation_id="test-missing-endpoint",
            causation_id="system-start",
            event_id="workflow-start",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            requested_by="tester",
            configuration={},
        )

        with pytest.raises(ConfigurationError) as exc_info:
            orchestrator._handle_workflow_started(event)

        assert "strategy endpoint is not configured" in str(exc_info.value).lower()

    def test_http_workflow_disabled_skips_endpoint_checks(self) -> None:
        """Test that HTTP workflow disabled mode doesn't check endpoints."""
        container = ApplicationContainer.create_for_testing()
        custom_settings = Settings()
        custom_settings.orchestration.use_http_domain_workflow = False
        custom_settings.orchestration.strategy_endpoint = ""  # Not configured, but OK
        container.config.settings.override(providers.Object(custom_settings))

        orchestrator = EventDrivenOrchestrator(container)

        event = WorkflowStarted(
            correlation_id="test-disabled",
            causation_id="system-start",
            event_id="workflow-start",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            requested_by="tester",
            configuration={},
        )

        # Should not raise - HTTP workflow is disabled
        orchestrator._handle_workflow_started(event)


class TestHttpHandlerErrorPropagation:
    """Tests for error propagation in HTTP workflow handlers."""

    def test_handler_propagates_http_errors_with_context(self) -> None:
        """Test that HTTP errors in handlers are logged and propagated."""
        container = ApplicationContainer.create_for_testing()
        custom_settings = Settings()
        custom_settings.orchestration.use_http_domain_workflow = True
        custom_settings.orchestration.strategy_endpoint = "http://strategy.local/signals"
        container.config.settings.override(providers.Object(custom_settings))

        # Mock HTTP client that fails
        def failing_transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "Internal Server Error"})

        http_client = httpx.Client(transport=httpx.MockTransport(failing_transport))
        orchestrator = EventDrivenOrchestrator(container, http_client=http_client)

        event = WorkflowStarted(
            correlation_id="test-error-propagation",
            causation_id="system-start",
            event_id="workflow-start",
            timestamp=datetime.now(UTC),
            source_module="test",
            source_component="test",
            workflow_type="trading",
            requested_by="tester",
            configuration={},
        )

        # Should propagate the HTTP error after retries
        with pytest.raises(httpx.HTTPStatusError):
            orchestrator._handle_workflow_started(event)


class TestPublishHttpEvent:
    """Tests for _publish_http_event method."""

    def test_logs_error_when_deserialization_returns_none(self) -> None:
        """Test that _publish_http_event logs error when deserialization fails."""
        container = ApplicationContainer.create_for_testing()
        orchestrator = EventDrivenOrchestrator(container)

        # Malformed payload
        payload: dict[str, Any] = {
            "correlation_id": "test-malformed",
            "event_type": "UnknownType",  # Will fail deserialization
        }

        # Should not raise, but should log error
        orchestrator._publish_http_event(payload)
        # Note: In a real test, we'd capture logs to verify error was logged
