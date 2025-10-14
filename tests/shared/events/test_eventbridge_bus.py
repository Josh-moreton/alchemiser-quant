#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for EventBridgeBus implementation.

Tests cover:
- Event publishing to EventBridge
- Event serialization and deserialization
- Error handling and logging
- Local handler support for testing
- Client initialization
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.events import BaseEvent, SignalGenerated
from the_alchemiser.shared.events.eventbridge_bus import EventBridgeBus


@pytest.fixture
def mock_events_client() -> Mock:
    """Create mock EventBridge client."""
    client = Mock()
    client.put_events.return_value = {"FailedEntryCount": 0, "Entries": [{"EventId": "test-id"}]}
    return client


@pytest.fixture
def eventbridge_bus(mock_events_client: Mock) -> EventBridgeBus:
    """Create EventBridgeBus with mocked client."""
    bus = EventBridgeBus(event_bus_name="test-bus", source_prefix="test")
    bus._events_client = mock_events_client
    return bus


@pytest.mark.unit
class TestEventBridgeBusInitialization:
    """Test EventBridgeBus initialization."""

    def test_init_with_explicit_bus_name(self) -> None:
        """Test initialization with explicit bus name."""
        bus = EventBridgeBus(event_bus_name="custom-bus", source_prefix="custom")

        assert bus.event_bus_name == "custom-bus"
        assert bus.source_prefix == "custom"
        assert bus.enable_local_handlers is False

    def test_init_with_environment_variable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test initialization reads from environment variable."""
        monkeypatch.setenv("EVENTBRIDGE_BUS_NAME", "env-bus")

        bus = EventBridgeBus()

        assert bus.event_bus_name == "env-bus"

    def test_init_with_default_bus_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test initialization uses default when no env var."""
        monkeypatch.delenv("EVENTBRIDGE_BUS_NAME", raising=False)

        bus = EventBridgeBus()

        assert bus.event_bus_name == "alchemiser-trading-events-dev"

    def test_init_with_local_handlers_enabled(self) -> None:
        """Test initialization with local handlers enabled."""
        bus = EventBridgeBus(enable_local_handlers=True)

        assert bus.enable_local_handlers is True

    @patch("boto3.client")
    def test_lazy_client_initialization(self, mock_boto3_client: Mock) -> None:
        """Test EventBridge client is lazily initialized."""
        bus = EventBridgeBus()

        # Client not created yet
        assert bus._events_client is None

        # Access client property
        _ = bus.events_client

        # Now client is created
        mock_boto3_client.assert_called_once_with("events")


@pytest.mark.unit
class TestEventBridgeBusPublish:
    """Test event publishing to EventBridge."""

    def test_publish_event_success(
        self, eventbridge_bus: EventBridgeBus, mock_events_client: Mock
    ) -> None:
        """Test successful event publishing."""
        event = SignalGenerated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            signals_data={"BTC": 0.5},
            consolidated_portfolio={"BTC": 0.5},
            signal_count=1,
        )

        eventbridge_bus.publish(event)

        # Verify put_events was called
        mock_events_client.put_events.assert_called_once()
        call_args = mock_events_client.put_events.call_args[1]

        # Verify entry structure
        entries = call_args["Entries"]
        assert len(entries) == 1

        entry = entries[0]
        assert entry["Source"] == "test.strategy"
        assert entry["DetailType"] == "SignalGenerated"
        assert entry["EventBusName"] == "test-bus"
        assert "correlation:corr-123" in entry["Resources"]
        assert "causation:cause-123" in entry["Resources"]

        # Verify detail is valid JSON
        detail = json.loads(entry["Detail"])
        assert detail["event_id"] == "event-123"
        assert detail["correlation_id"] == "corr-123"
        assert detail["signal_count"] == 1

    def test_publish_event_verifies_resources(
        self, eventbridge_bus: EventBridgeBus, mock_events_client: Mock
    ) -> None:
        """Test that correlation and causation IDs are added to Resources."""
        event = SignalGenerated(
            correlation_id="corr-123",
            causation_id="cause-456",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
        )

        eventbridge_bus.publish(event)

        call_args = mock_events_client.put_events.call_args[1]
        entry = call_args["Entries"][0]

        assert "correlation:corr-123" in entry["Resources"]
        assert "causation:cause-456" in entry["Resources"]

    def test_publish_event_failure(
        self, eventbridge_bus: EventBridgeBus, mock_events_client: Mock
    ) -> None:
        """Test handling of EventBridge publish failure."""
        mock_events_client.put_events.return_value = {
            "FailedEntryCount": 1,
            "Entries": [{"ErrorCode": "InternalException", "ErrorMessage": "Test failure"}],
        }

        event = SignalGenerated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
        )

        # Should not raise, just log
        eventbridge_bus.publish(event)

        # Verify error was handled (didn't raise)

    def test_publish_event_with_exception(
        self, eventbridge_bus: EventBridgeBus, mock_events_client: Mock
    ) -> None:
        """Test handling of unexpected exception during publish."""
        mock_events_client.put_events.side_effect = Exception("Network error")

        event = SignalGenerated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
        )

        # Should not raise, just log
        eventbridge_bus.publish(event)

        # Verify error was handled (didn't raise)

    def test_publish_with_local_handlers_enabled(self) -> None:
        """Test publishing with local handlers enabled triggers both."""
        bus = EventBridgeBus(enable_local_handlers=True)
        mock_client = Mock()
        mock_client.put_events.return_value = {"FailedEntryCount": 0, "Entries": []}
        bus._events_client = mock_client

        # Subscribe local handler
        handler_called = False

        def handler(event: BaseEvent) -> None:
            nonlocal handler_called
            handler_called = True

        bus.subscribe("SignalGenerated", handler)

        event = SignalGenerated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
        )

        bus.publish(event)

        # Verify both EventBridge and local handler were called
        mock_client.put_events.assert_called_once()
        assert handler_called

    def test_publish_serializes_decimal_correctly(
        self, eventbridge_bus: EventBridgeBus, mock_events_client: Mock
    ) -> None:
        """Test that Decimal values are serialized correctly."""

        class TestEvent(BaseEvent):
            event_type: str = "TestEvent"
            value: Decimal

        event = TestEvent(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="test",
            value=Decimal("123.45"),
        )

        eventbridge_bus.publish(event)

        call_args = mock_events_client.put_events.call_args[1]
        detail_str = call_args["Entries"][0]["Detail"]
        detail = json.loads(detail_str)

        # Decimal should be serialized as string
        assert detail["value"] == "123.45"


@pytest.mark.unit
class TestEventBridgeBusSubscribe:
    """Test event subscription behavior."""

    def test_subscribe_without_local_handlers_warns(self) -> None:
        """Test subscribing without local handlers logs warning."""
        bus = EventBridgeBus(enable_local_handlers=False)

        def handler(event: BaseEvent) -> None:
            pass

        # This should not raise but will log a warning
        bus.subscribe("SignalGenerated", handler)

    def test_subscribe_with_local_handlers_works(self) -> None:
        """Test subscribing with local handlers enabled works."""
        bus = EventBridgeBus(enable_local_handlers=True)

        def handler(event: BaseEvent) -> None:
            pass

        # Should not raise
        bus.subscribe("SignalGenerated", handler)

        # Verify handler registered
        assert bus.get_handler_count("SignalGenerated") == 1


@pytest.mark.unit
class TestEventBridgeBusInheritance:
    """Test EventBridgeBus inheritance from EventBus."""

    def test_inherits_from_eventbus(self) -> None:
        """Test EventBridgeBus inherits from EventBus."""
        from the_alchemiser.shared.events.bus import EventBus

        bus = EventBridgeBus()
        assert isinstance(bus, EventBus)

    def test_get_handler_count_with_local_handlers(self) -> None:
        """Test get_handler_count works with local handlers."""
        bus = EventBridgeBus(enable_local_handlers=True)

        def handler(event: BaseEvent) -> None:
            pass

        bus.subscribe("SignalGenerated", handler)
        bus.subscribe("RebalancePlanned", handler)

        assert bus.get_handler_count("SignalGenerated") == 1
        assert bus.get_handler_count("RebalancePlanned") == 1
        assert bus.get_handler_count() == 2

    def test_get_event_count(self) -> None:
        """Test get_event_count tracks published events."""
        bus = EventBridgeBus()
        mock_client = Mock()
        mock_client.put_events.return_value = {"FailedEntryCount": 0, "Entries": []}
        bus._events_client = mock_client

        assert bus.get_event_count() == 0

        event = SignalGenerated(
            correlation_id="corr-123",
            causation_id="cause-123",
            event_id="event-123",
            timestamp=datetime.now(UTC),
            source_module="strategy",
            signals_data={},
            consolidated_portfolio={},
            signal_count=0,
        )

        bus.publish(event)
        assert bus.get_event_count() == 1

        bus.publish(event)
        assert bus.get_event_count() == 2
