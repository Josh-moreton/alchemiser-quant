"""Business Unit: strategy | Status: current.

Test strategy_v2 module imports and public API.

Tests that the module's public API exports work correctly and
event handler registration functions as expected.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from the_alchemiser import strategy_v2
from the_alchemiser.strategy_v2 import (
    SingleStrategyOrchestrator,
    StrategyContext,
    get_strategy,
    list_strategies,
    register_strategy,
    register_strategy_handlers,
)


class TestStrategyV2ModuleImports:
    """Test strategy_v2 module imports and exports."""

    def test_import_register_strategy_handlers(self) -> None:
        """Test importing register_strategy_handlers function."""
        from the_alchemiser.strategy_v2 import register_strategy_handlers

        assert register_strategy_handlers is not None
        assert callable(register_strategy_handlers)

    def test_import_single_strategy_orchestrator(self) -> None:
        """Test importing SingleStrategyOrchestrator from module."""
        from the_alchemiser.strategy_v2 import SingleStrategyOrchestrator

        assert SingleStrategyOrchestrator is not None
        assert hasattr(SingleStrategyOrchestrator, "__init__")

    def test_import_strategy_context(self) -> None:
        """Test importing StrategyContext from module."""
        from the_alchemiser.strategy_v2 import StrategyContext

        assert StrategyContext is not None
        # StrategyContext is a dataclass, not a regular class
        assert hasattr(StrategyContext, "__dataclass_fields__")

    def test_import_registry_functions(self) -> None:
        """Test importing registry functions from module."""
        from the_alchemiser.strategy_v2 import get_strategy, list_strategies, register_strategy

        assert get_strategy is not None
        assert callable(get_strategy)
        assert list_strategies is not None
        assert callable(list_strategies)
        assert register_strategy is not None
        assert callable(register_strategy)

    def test_getattr_single_strategy_orchestrator(self) -> None:
        """Test __getattr__ for SingleStrategyOrchestrator."""
        orchestrator_class = getattr(strategy_v2, "SingleStrategyOrchestrator")
        assert orchestrator_class is not None

    def test_getattr_strategy_context(self) -> None:
        """Test __getattr__ for StrategyContext."""
        context_class = getattr(strategy_v2, "StrategyContext")
        assert context_class is not None

    def test_getattr_get_strategy(self) -> None:
        """Test __getattr__ for get_strategy."""
        func = getattr(strategy_v2, "get_strategy")
        assert func is not None
        assert callable(func)

    def test_getattr_list_strategies(self) -> None:
        """Test __getattr__ for list_strategies."""
        func = getattr(strategy_v2, "list_strategies")
        assert func is not None
        assert callable(func)

    def test_getattr_register_strategy(self) -> None:
        """Test __getattr__ for register_strategy."""
        func = getattr(strategy_v2, "register_strategy")
        assert func is not None
        assert callable(func)

    def test_getattr_invalid_attribute(self) -> None:
        """Test __getattr__ raises AttributeError for invalid attributes."""
        with pytest.raises(AttributeError) as exc_info:
            _ = getattr(strategy_v2, "NonExistentAttribute")

        assert "has no attribute" in str(exc_info.value)
        assert "NonExistentAttribute" in str(exc_info.value)
        # Verify improved error message includes available attributes
        assert "Available attributes:" in str(exc_info.value)

    def test_all_exports_defined(self) -> None:
        """Test that __all__ is defined and contains expected exports."""
        assert hasattr(strategy_v2, "__all__")
        expected_exports = {
            "SingleStrategyOrchestrator",
            "StrategyContext",
            "get_strategy",
            "list_strategies",
            "register_strategy",
            "register_strategy_handlers",
        }
        actual_exports = set(strategy_v2.__all__)
        assert actual_exports == expected_exports

    def test_version_defined(self) -> None:
        """Test that module version is defined."""
        assert hasattr(strategy_v2, "__version__")
        assert isinstance(strategy_v2.__version__, str)
        # Verify semantic versioning format (basic check)
        parts = strategy_v2.__version__.split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()

    def test_module_docstring_present(self) -> None:
        """Test that module has proper docstring with business unit identifier."""
        assert strategy_v2.__doc__ is not None
        assert len(strategy_v2.__doc__) > 0
        assert "Business Unit: strategy" in strategy_v2.__doc__
        assert "Status: current" in strategy_v2.__doc__


class TestRegisterStrategyHandlers:
    """Test event handler registration functionality."""

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Create a mock ApplicationContainer for testing."""
        container = Mock()
        container.services.event_bus = Mock(return_value=Mock())
        return container

    def test_register_strategy_handlers_callable(self) -> None:
        """Test that register_strategy_handlers is callable."""
        assert callable(register_strategy_handlers)

    def test_register_strategy_handlers_creates_handler_instance(
        self, mock_container: Mock
    ) -> None:
        """Test that register_strategy_handlers creates SignalGenerationHandler."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_strategy_handlers(mock_container)

        # Verify handler was created and subscribed
        assert mock_event_bus.subscribe.called
        handler = mock_event_bus.subscribe.call_args_list[0][0][1]

        # Handler should have the expected interface
        assert hasattr(handler, "handle_event")
        assert hasattr(handler, "can_handle")
        assert callable(handler.handle_event)
        assert callable(handler.can_handle)

    def test_register_strategy_handlers_subscribes_to_startup_event(
        self, mock_container: Mock
    ) -> None:
        """Test that register_strategy_handlers subscribes to StartupEvent."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_strategy_handlers(mock_container)

        # Verify subscribe was called with StartupEvent
        call_args_list = mock_event_bus.subscribe.call_args_list
        event_types = [call[0][0] for call in call_args_list]

        assert "StartupEvent" in event_types

    def test_register_strategy_handlers_subscribes_to_workflow_started(
        self, mock_container: Mock
    ) -> None:
        """Test that register_strategy_handlers subscribes to WorkflowStarted."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_strategy_handlers(mock_container)

        # Verify subscribe was called with WorkflowStarted
        call_args_list = mock_event_bus.subscribe.call_args_list
        event_types = [call[0][0] for call in call_args_list]

        assert "WorkflowStarted" in event_types

    def test_registered_handler_can_handle_startup_event(self, mock_container: Mock) -> None:
        """Test that registered handler can handle StartupEvent events."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_strategy_handlers(mock_container)

        # Get the registered handler
        handler = mock_event_bus.subscribe.call_args_list[0][0][1]

        # Verify it can handle the correct event type
        assert handler.can_handle("StartupEvent") is True

    def test_registered_handler_can_handle_workflow_started(
        self, mock_container: Mock
    ) -> None:
        """Test that registered handler can handle WorkflowStarted events."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_strategy_handlers(mock_container)

        # Get the registered handler
        handler = mock_event_bus.subscribe.call_args_list[0][0][1]

        # Verify it can handle the correct event type
        assert handler.can_handle("WorkflowStarted") is True

    def test_register_strategy_handlers_gets_event_bus_from_container(
        self, mock_container: Mock
    ) -> None:
        """Test that register_strategy_handlers gets event bus from container."""
        # Register handlers
        register_strategy_handlers(mock_container)

        # Verify event bus was obtained from container (at least once)
        assert mock_container.services.event_bus.called
        assert mock_container.services.event_bus.call_count >= 1

    def test_register_strategy_handlers_subscribes_same_handler_twice(
        self, mock_container: Mock
    ) -> None:
        """Test that register_strategy_handlers subscribes same handler to both events."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_strategy_handlers(mock_container)

        # Get handlers from both subscriptions
        call_args_list = mock_event_bus.subscribe.call_args_list
        handlers = [call[0][1] for call in call_args_list]

        # Verify same handler instance used for both subscriptions
        assert len(handlers) == 2
        assert handlers[0] is handlers[1]

    def test_register_strategy_handlers_validates_container(self) -> None:
        """Test that register_strategy_handlers validates container has services attribute."""
        from the_alchemiser.shared.errors import ConfigurationError

        # Create invalid container without services attribute
        invalid_container = Mock(spec=[])  # Empty spec means no attributes

        with pytest.raises(ConfigurationError) as exc_info:
            register_strategy_handlers(invalid_container)

        assert "Container missing required 'services' attribute" in str(exc_info.value)

    def test_register_strategy_handlers_handles_event_bus_error(
        self, mock_container: Mock
    ) -> None:
        """Test that register_strategy_handlers handles errors from event_bus()."""
        # Make event_bus() raise an exception
        mock_container.services.event_bus.side_effect = RuntimeError("Event bus error")

        with pytest.raises(RuntimeError) as exc_info:
            register_strategy_handlers(mock_container)

        assert "Event bus error" in str(exc_info.value)

    def test_register_strategy_handlers_handles_handler_init_error(
        self, mock_container: Mock
    ) -> None:
        """Test that register_strategy_handlers handles errors from handler initialization."""
        from unittest.mock import patch

        # Mock SignalGenerationHandler to raise an error
        with patch(
            "the_alchemiser.strategy_v2.handlers.SignalGenerationHandler",
            side_effect=ValueError("Handler init error"),
        ):
            with pytest.raises(ValueError) as exc_info:
                register_strategy_handlers(mock_container)

            assert "Handler init error" in str(exc_info.value)

    def test_register_strategy_handlers_handles_subscribe_error(
        self, mock_container: Mock
    ) -> None:
        """Test that register_strategy_handlers handles errors from subscribe()."""
        mock_event_bus = mock_container.services.event_bus.return_value
        # Make subscribe() raise an exception
        mock_event_bus.subscribe.side_effect = RuntimeError("Subscribe error")

        with pytest.raises(RuntimeError) as exc_info:
            register_strategy_handlers(mock_container)

        assert "Subscribe error" in str(exc_info.value)
