"""Business Unit: shared | Status: current.

Tests for EventHandler protocol validation.

Validates the EventHandler protocol structure, runtime_checkable behavior,
and proper isinstance() validation patterns.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.handlers import EventHandler


class MockEvent(BaseEvent):
    """Mock event for testing."""

    def __init__(self, event_type: str = "test_event", **kwargs: Any) -> None:
        """Initialize mock event with required fields."""
        defaults: dict[str, str | datetime] = {
            "correlation_id": "test-correlation-123",
            "causation_id": "test-causation-456",
            "event_id": "test-event-789",
            "timestamp": datetime.now(UTC),
            "source_module": "test_module",
        }
        defaults.update(kwargs)
        super().__init__(event_type=event_type, **defaults)


class ValidHandler:
    """Handler that properly implements EventHandler protocol."""

    def handle_event(self, event: BaseEvent) -> None:
        """Handle an event."""

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle event type."""
        return True


class InvalidHandlerMissingHandleEvent:
    """Handler missing handle_event method."""

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle event type."""
        return True


class InvalidHandlerMissingCanHandle:
    """Handler missing can_handle method."""

    def handle_event(self, event: BaseEvent) -> None:
        """Handle an event."""


class InvalidHandlerWrongSignature:
    """Handler with wrong method signature."""

    def handle_event(self, event: BaseEvent, extra_param: str) -> None:
        """Handle an event with wrong signature."""

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle event type."""
        return True


def test_protocol_is_runtime_checkable() -> None:
    """Test that EventHandler protocol is runtime_checkable."""
    valid_handler = ValidHandler()

    # Protocol should enable isinstance() checks
    assert isinstance(valid_handler, EventHandler)


def test_protocol_rejects_invalid_handler_missing_handle_event() -> None:
    """Test that protocol rejects handler missing handle_event."""
    invalid_handler = InvalidHandlerMissingHandleEvent()

    # Should not be considered valid EventHandler
    assert not isinstance(invalid_handler, EventHandler)


def test_protocol_rejects_invalid_handler_missing_can_handle() -> None:
    """Test that protocol rejects handler missing can_handle."""
    invalid_handler = InvalidHandlerMissingCanHandle()

    # Should not be considered valid EventHandler
    assert not isinstance(invalid_handler, EventHandler)


def test_protocol_validates_method_presence_not_signature() -> None:
    """Test that protocol checks method presence but not exact signature.

    Python's Protocol checks for method existence but doesn't enforce
    exact signature matching at runtime (that's what mypy does).
    """
    # Handler with extra parameter still passes isinstance check
    # (mypy would catch this as a type error)
    handler_wrong_sig = InvalidHandlerWrongSignature()

    # isinstance only checks method existence, not signature
    assert isinstance(handler_wrong_sig, EventHandler)


def test_valid_handler_can_handle_events() -> None:
    """Test that valid handler can be used with protocol interface."""
    handler = ValidHandler()
    event = MockEvent()

    # Should be able to call protocol methods
    assert handler.can_handle("test_event") is True
    handler.handle_event(event)  # Should not raise


def test_protocol_handler_methods_are_defined() -> None:
    """Test that EventHandler protocol has expected methods."""
    # Protocol should define these methods
    assert hasattr(EventHandler, "handle_event")
    assert hasattr(EventHandler, "can_handle")


def test_protocol_can_be_used_as_type_hint() -> None:
    """Test that EventHandler can be used as a type hint."""

    def accepts_handler(handler: EventHandler) -> bool:
        """Accept EventHandler type and validate it."""
        return isinstance(handler, EventHandler)

    valid_handler = ValidHandler()
    assert accepts_handler(valid_handler) is True


def test_protocol_usage_with_list_of_handlers() -> None:
    """Test protocol usage pattern for storing multiple handlers."""
    handlers: list[EventHandler] = []

    # Should be able to add valid handlers to typed list
    handlers.append(ValidHandler())
    handlers.append(ValidHandler())

    assert len(handlers) == 2
    for handler in handlers:
        assert isinstance(handler, EventHandler)


def test_protocol_method_handle_event_signature() -> None:
    """Test that handle_event has correct parameter expectations."""
    handler = ValidHandler()
    event = MockEvent(event_type="custom_event")

    # Should accept BaseEvent and return None
    handler.handle_event(event)
    # No assertion needed - method returns None implicitly


def test_protocol_method_can_handle_signature() -> None:
    """Test that can_handle has correct parameter expectations."""
    handler = ValidHandler()

    # Should accept string and return boolean
    result = handler.can_handle("test_event")
    assert isinstance(result, bool)


def test_protocol_enables_polymorphic_behavior() -> None:
    """Test that protocol enables polymorphic handler usage."""

    class HandlerA:
        def handle_event(self, event: BaseEvent) -> None:
            self.handled = "A"

        def can_handle(self, event_type: str) -> bool:
            return event_type == "type_a"

    class HandlerB:
        def handle_event(self, event: BaseEvent) -> None:
            self.handled = "B"

        def can_handle(self, event_type: str) -> bool:
            return event_type == "type_b"

    # Both should be valid EventHandlers
    handler_a = HandlerA()
    handler_b = HandlerB()

    assert isinstance(handler_a, EventHandler)
    assert isinstance(handler_b, EventHandler)

    # Can be stored in polymorphic collection
    handlers: list[EventHandler] = [handler_a, handler_b]

    event = MockEvent()
    for handler in handlers:
        handler.handle_event(event)
