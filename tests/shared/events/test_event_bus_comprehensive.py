"""Business Unit: shared | Status: current

Comprehensive unit tests for the event bus system.

This test suite provides full coverage of the event bus functionality including
subscription, publishing, error handling, and edge cases.
"""

from datetime import UTC, datetime

import pytest

from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.bus import EventBus


class MockEvent(BaseEvent):
    """Mock event for testing purposes."""

    def __init__(self, event_type: str = "mock_event", **kwargs):
        # Use default values for required fields if not provided
        defaults = {
            "correlation_id": "test-correlation-123",
            "causation_id": "test-causation-456",
            "event_id": "test-event-789",
            "timestamp": datetime.now(UTC),
            "source_module": "test_module",
        }
        defaults.update(kwargs)
        super().__init__(event_type=event_type, **defaults)


class MockHandler:
    """Mock handler that implements the EventHandler protocol."""

    def __init__(self):
        self.handled_events = []
        self.call_count = 0

    def handle_event(self, event: BaseEvent) -> None:
        """Handle an event by recording it."""
        self.handled_events.append(event)
        self.call_count += 1

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type."""
        return True  # For simplicity, handle all events


class TestEventBusInitialization:
    """Test event bus initialization and basic state."""

    def test_event_bus_initializes_correctly(self):
        """Test that event bus initializes with correct state."""
        bus = EventBus()

        assert bus._event_count == 0
        assert len(bus._handlers) == 0
        assert len(bus._global_handlers) == 0

    def test_event_bus_has_logger(self):
        """Test that event bus has a logger instance."""
        bus = EventBus()
        assert hasattr(bus, "logger")
        assert bus.logger is not None


class TestEventBusSubscription:
    """Test event bus subscription functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bus = EventBus()
        self.handler = MockHandler()

    def test_subscribe_to_specific_event_type(self):
        """Test subscribing a handler to a specific event type."""
        self.bus.subscribe("test_event", self.handler)

        assert "test_event" in self.bus._handlers
        assert self.handler in self.bus._handlers["test_event"]

    def test_subscribe_multiple_handlers_to_same_event(self):
        """Test subscribing multiple handlers to the same event type."""
        handler2 = MockHandler()

        self.bus.subscribe("test_event", self.handler)
        self.bus.subscribe("test_event", handler2)

        assert len(self.bus._handlers["test_event"]) == 2
        assert self.handler in self.bus._handlers["test_event"]
        assert handler2 in self.bus._handlers["test_event"]

    def test_subscribe_empty_event_type_raises_error(self):
        """Test that subscribing with empty event type raises ValueError."""
        with pytest.raises(ValueError, match="Event type cannot be empty"):
            self.bus.subscribe("", self.handler)

        with pytest.raises(ValueError, match="Event type cannot be empty"):
            self.bus.subscribe("   ", self.handler)

    def test_subscribe_invalid_handler_raises_error(self):
        """Test that subscribing with invalid handler raises ValueError."""
        with pytest.raises(ValueError, match="Handler must implement EventHandler protocol"):
            self.bus.subscribe("test_event", "not_a_handler")

        with pytest.raises(ValueError, match="Handler must implement EventHandler protocol"):
            self.bus.subscribe("test_event", None)

    def test_subscribe_global_handler(self):
        """Test subscribing a global handler."""
        self.bus.subscribe_global(self.handler)

        assert self.handler in self.bus._global_handlers

    def test_subscribe_global_invalid_handler_raises_error(self):
        """Test that subscribing invalid global handler raises ValueError."""
        with pytest.raises(ValueError, match="Handler must implement EventHandler protocol"):
            self.bus.subscribe_global("not_a_handler")


class TestEventBusUnsubscription:
    """Test event bus unsubscription functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bus = EventBus()
        self.handler = MockHandler()

    def test_unsubscribe_existing_handler(self):
        """Test unsubscribing an existing handler."""
        self.bus.subscribe("test_event", self.handler)
        assert self.handler in self.bus._handlers["test_event"]

        self.bus.unsubscribe("test_event", self.handler)
        assert self.handler not in self.bus._handlers["test_event"]

    def test_unsubscribe_nonexistent_handler_logs_warning(self):
        """Test that unsubscribing nonexistent handler logs warning."""
        # Subscribe to establish the event type
        self.bus.subscribe("test_event", MockHandler())

        # Try to unsubscribe a handler that was never subscribed
        self.bus.unsubscribe("test_event", self.handler)
        # Should not raise an error, just log a warning

    def test_unsubscribe_from_nonexistent_event_type(self):
        """Test unsubscribing from nonexistent event type."""
        # Should not raise an error
        self.bus.unsubscribe("nonexistent_event", self.handler)

    def test_unsubscribe_global_handler(self):
        """Test unsubscribing a global handler."""
        self.bus.subscribe_global(self.handler)
        assert self.handler in self.bus._global_handlers

        self.bus.unsubscribe_global(self.handler)
        assert self.handler not in self.bus._global_handlers

    def test_unsubscribe_global_nonexistent_handler_logs_warning(self):
        """Test that unsubscribing nonexistent global handler logs warning."""
        # Try to unsubscribe a global handler that was never subscribed
        self.bus.unsubscribe_global(self.handler)
        # Should not raise an error, just log a warning


class TestEventBusPublishing:
    """Test event bus publishing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bus = EventBus()
        self.handler = MockHandler()
        self.global_handler = MockHandler()

    def test_publish_event_to_specific_handlers(self):
        """Test publishing event to specific event type handlers."""
        self.bus.subscribe("test_event", self.handler)

        event = MockEvent("test_event")
        self.bus.publish(event)

        assert self.handler.call_count == 1
        assert event in self.handler.handled_events

    def test_publish_event_to_global_handlers(self):
        """Test that events are published to global handlers."""
        self.bus.subscribe_global(self.global_handler)

        event = MockEvent("any_event")
        self.bus.publish(event)

        assert self.global_handler.call_count == 1
        assert event in self.global_handler.handled_events

    def test_publish_event_to_both_specific_and_global_handlers(self):
        """Test that events are published to both specific and global handlers."""
        self.bus.subscribe("test_event", self.handler)
        self.bus.subscribe_global(self.global_handler)

        event = MockEvent("test_event")
        self.bus.publish(event)

        assert self.handler.call_count == 1
        assert self.global_handler.call_count == 1
        assert event in self.handler.handled_events
        assert event in self.global_handler.handled_events

    def test_publish_increments_event_count(self):
        """Test that publishing increments the event count."""
        initial_count = self.bus._event_count

        event = MockEvent("test_event")
        self.bus.publish(event)

        assert self.bus._event_count == initial_count + 1

    def test_publish_invalid_event_raises_error(self):
        """Test that publishing invalid event raises ValueError."""
        with pytest.raises(ValueError, match="Event must be a BaseEvent instance"):
            self.bus.publish("not_an_event")

        with pytest.raises(ValueError, match="Event must be a BaseEvent instance"):
            self.bus.publish(None)

    def test_publish_to_no_handlers(self):
        """Test publishing when no handlers are subscribed."""
        event = MockEvent("unhandled_event")

        # Should not raise an error
        self.bus.publish(event)
        assert self.bus._event_count == 1

    def test_publish_multiple_events_maintains_count(self):
        """Test that publishing multiple events maintains correct count."""
        events = [MockEvent("event1"), MockEvent("event2"), MockEvent("event3")]

        for event in events:
            self.bus.publish(event)

        assert self.bus._event_count == 3


class TestEventBusErrorHandling:
    """Test event bus error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bus = EventBus()

    def test_handler_exception_does_not_stop_other_handlers(self):
        """Test that exception in one handler doesn't stop others."""
        # Create handlers - one that throws, one that works
        failing_handler = MockHandler()
        working_handler = MockHandler()

        # Mock the failing handler to raise an exception
        original_handle = failing_handler.handle_event

        def failing_handle(event):
            original_handle(event)  # Still record the event
            raise Exception("Handler failed")

        failing_handler.handle_event = failing_handle

        self.bus.subscribe("test_event", failing_handler)
        self.bus.subscribe("test_event", working_handler)

        event = MockEvent("test_event")

        # This should not raise an exception
        self.bus.publish(event)

        # Both handlers should have been called
        assert failing_handler.call_count == 1
        assert working_handler.call_count == 1


class TestEventBusIntegration:
    """Test event bus integration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bus = EventBus()

    def test_complex_subscription_and_publishing_scenario(self):
        """Test complex scenario with multiple event types and handlers."""
        # Create multiple handlers
        handler1 = MockHandler()
        handler2 = MockHandler()
        global_handler = MockHandler()

        # Set up subscriptions
        self.bus.subscribe("event_a", handler1)
        self.bus.subscribe("event_b", handler2)
        self.bus.subscribe("event_a", handler2)  # handler2 also handles event_a
        self.bus.subscribe_global(global_handler)

        # Publish different events
        event_a = MockEvent("event_a")
        event_b = MockEvent("event_b")
        event_c = MockEvent("event_c")  # No specific handler

        self.bus.publish(event_a)
        self.bus.publish(event_b)
        self.bus.publish(event_c)

        # Check handler call counts
        assert handler1.call_count == 1  # Only event_a
        assert handler2.call_count == 2  # event_a and event_b
        assert global_handler.call_count == 3  # All events

        # Check events received
        assert event_a in handler1.handled_events
        assert event_a in handler2.handled_events
        assert event_b in handler2.handled_events
        assert all(event in global_handler.handled_events for event in [event_a, event_b, event_c])

    def test_unsubscribe_during_active_usage(self):
        """Test unsubscribing handlers during active usage."""
        handler1 = MockHandler()
        handler2 = MockHandler()

        self.bus.subscribe("test_event", handler1)
        self.bus.subscribe("test_event", handler2)

        # Publish first event
        event1 = MockEvent("test_event", event_id="event1")
        self.bus.publish(event1)

        assert handler1.call_count == 1
        assert handler2.call_count == 1

        # Unsubscribe handler1
        self.bus.unsubscribe("test_event", handler1)

        # Publish second event
        event2 = MockEvent("test_event", event_id="event2")
        self.bus.publish(event2)

        # Only handler2 should receive the second event
        assert handler1.call_count == 1  # Still 1
        assert handler2.call_count == 2  # Now 2

    def test_event_bus_state_consistency(self):
        """Test that event bus maintains consistent state."""
        handler = MockHandler()

        # Subscribe and check state
        self.bus.subscribe("test_event", handler)
        assert len(self.bus._handlers["test_event"]) == 1

        # Subscribe global and check state
        self.bus.subscribe_global(handler)
        assert len(self.bus._global_handlers) == 1

        # Publish and check state
        initial_count = self.bus._event_count
        self.bus.publish(MockEvent("test_event"))
        assert self.bus._event_count == initial_count + 1

        # Unsubscribe and check state
        self.bus.unsubscribe("test_event", handler)
        assert len(self.bus._handlers["test_event"]) == 0

        self.bus.unsubscribe_global(handler)
        assert len(self.bus._global_handlers) == 0
