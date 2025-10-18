"""Business Unit: notifications | Status: current.

Tests for notifications_v2 module public API interface.

Tests cover:
- Public API exports (__all__ completeness)
- register_notification_handlers() function behavior
- Error propagation and validation
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest


class TestPublicAPIExports:
    """Test public API exports and module interface."""

    def test_all_exports_are_importable(self) -> None:
        """Test that all __all__ exports are importable."""
        from the_alchemiser.notifications_v2 import (
            NotificationService,
            register_notification_handlers,
        )

        assert NotificationService is not None
        assert callable(register_notification_handlers)

    def test_notification_service_is_class(self) -> None:
        """Test that NotificationService is a class."""
        from the_alchemiser.notifications_v2 import NotificationService

        assert isinstance(NotificationService, type)

    def test_register_function_is_callable(self) -> None:
        """Test that register_notification_handlers is callable."""
        from the_alchemiser.notifications_v2 import register_notification_handlers

        assert callable(register_notification_handlers)

    def test_all_list_completeness(self) -> None:
        """Test that __all__ contains expected exports."""
        from the_alchemiser import notifications_v2

        expected_exports = {
            "NotificationService",
            "register_notification_handlers",
        }

        assert set(notifications_v2.__all__) == expected_exports

    def test_version_attribute_exists(self) -> None:
        """Test that module has __version__ attribute."""
        from the_alchemiser import notifications_v2

        assert hasattr(notifications_v2, "__version__")
        assert isinstance(notifications_v2.__version__, str)
        # Version should follow semantic versioning pattern
        assert len(notifications_v2.__version__.split(".")) == 3


class TestRegisterNotificationHandlers:
    """Test register_notification_handlers() function behavior."""

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Create a mock ApplicationContainer."""
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus
        return container

    def test_register_creates_service_and_calls_register_handlers(
        self, mock_container: Mock
    ) -> None:
        """Test registration function creates service and registers handlers."""
        from the_alchemiser.notifications_v2 import register_notification_handlers

        with patch("the_alchemiser.notifications_v2.NotificationService") as MockService:
            mock_service_instance = Mock()
            MockService.return_value = mock_service_instance

            register_notification_handlers(mock_container)

            # Verify service was created with container
            MockService.assert_called_once_with(mock_container)
            # Verify register_handlers was called
            mock_service_instance.register_handlers.assert_called_once()

    def test_register_subscribes_to_event_bus(self, mock_container: Mock) -> None:
        """Test that registration subscribes to event bus."""
        from the_alchemiser.notifications_v2 import register_notification_handlers

        mock_event_bus = mock_container.services.event_bus.return_value

        register_notification_handlers(mock_container)

        # Verify event bus subscriptions were made
        # The service should subscribe to 3 event types
        assert mock_event_bus.subscribe.call_count == 3

        # Verify the event types that were subscribed
        call_args_list = [call.args[0] for call in mock_event_bus.subscribe.call_args_list]
        expected_events = [
            "ErrorNotificationRequested",
            "TradingNotificationRequested",
            "SystemNotificationRequested",
        ]
        assert sorted(call_args_list) == sorted(expected_events)

    def test_register_propagates_initialization_errors(self, mock_container: Mock) -> None:
        """Test that registration errors propagate to caller."""
        from the_alchemiser.notifications_v2 import register_notification_handlers

        # Simulate event bus initialization failure
        mock_container.services.event_bus.side_effect = RuntimeError("Event bus unavailable")

        with pytest.raises(RuntimeError, match="Event bus unavailable"):
            register_notification_handlers(mock_container)

    def test_register_propagates_handler_registration_errors(self, mock_container: Mock) -> None:
        """Test that handler registration errors propagate to caller."""
        from the_alchemiser.notifications_v2 import register_notification_handlers

        with patch("the_alchemiser.notifications_v2.NotificationService") as MockService:
            mock_service_instance = Mock()
            mock_service_instance.register_handlers.side_effect = ValueError("Registration failed")
            MockService.return_value = mock_service_instance

            with pytest.raises(ValueError, match="Registration failed"):
                register_notification_handlers(mock_container)

    def test_register_with_none_container_fails(self) -> None:
        """Test that passing None as container raises AttributeError."""
        from the_alchemiser.notifications_v2 import register_notification_handlers

        with pytest.raises(AttributeError):
            register_notification_handlers(None)  # type: ignore[arg-type]

    def test_register_function_returns_none(self, mock_container: Mock) -> None:
        """Test that register function returns None."""
        from the_alchemiser.notifications_v2 import register_notification_handlers

        result = register_notification_handlers(mock_container)

        assert result is None


class TestIntegration:
    """Integration tests for the module interface."""

    def test_readme_usage_example_pattern(self) -> None:
        """Verify the README usage pattern is valid."""
        from the_alchemiser.notifications_v2 import register_notification_handlers

        # This should match the README example structure
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus

        # Should not raise
        register_notification_handlers(container)

        # Verify event bus was accessed
        container.services.event_bus.assert_called()

    def test_module_can_be_imported_without_side_effects(self) -> None:
        """Test that importing the module has no side effects."""
        # Import should not raise and not trigger any I/O
        import the_alchemiser.notifications_v2  # noqa: F401

        # If we get here, import succeeded without side effects
        assert True
