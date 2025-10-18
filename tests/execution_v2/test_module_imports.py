"""Business Unit: execution | Status: current

Test execution_v2 module imports and public API.

Tests that the module's public API exports work correctly and
event handler registration functions as expected.
"""

from unittest.mock import Mock

import pytest

from the_alchemiser import execution_v2
from the_alchemiser.execution_v2 import (
    ExecutionManager,
    ExecutionResult,
    TradeLedgerService,
    register_execution_handlers,
)


class TestExecutionV2ModuleImports:
    """Test execution_v2 module imports and exports."""

    def test_import_execution_manager(self):
        """Test importing ExecutionManager from module."""
        assert ExecutionManager is not None
        assert hasattr(ExecutionManager, "__init__")

    def test_import_execution_result(self):
        """Test importing ExecutionResult from module."""
        assert ExecutionResult is not None
        # ExecutionResult is a DTO, check for Pydantic model
        assert hasattr(ExecutionResult, "model_fields") or hasattr(ExecutionResult, "__init__")

    def test_import_trade_ledger_service(self):
        """Test importing TradeLedgerService from module."""
        assert TradeLedgerService is not None
        assert hasattr(TradeLedgerService, "__init__")

    def test_import_register_execution_handlers(self):
        """Test importing register_execution_handlers function."""
        from the_alchemiser.execution_v2 import register_execution_handlers

        assert register_execution_handlers is not None
        assert callable(register_execution_handlers)

    def test_getattr_execution_manager(self):
        """Test __getattr__ for ExecutionManager."""
        manager_class = execution_v2.ExecutionManager
        assert manager_class is not None

    def test_getattr_execution_result(self):
        """Test __getattr__ for ExecutionResult."""
        result_class = execution_v2.ExecutionResult
        assert result_class is not None

    def test_getattr_trade_ledger_service(self):
        """Test __getattr__ for TradeLedgerService."""
        service_class = execution_v2.TradeLedgerService
        assert service_class is not None

    def test_getattr_invalid_attribute_raises_error(self):
        """Test __getattr__ raises AttributeError for invalid attribute."""
        with pytest.raises(AttributeError) as exc_info:
            execution_v2.NonExistentClass

        assert "NonExistentClass" in str(exc_info.value)

    def test_all_contains_expected_exports(self):
        """Test __all__ contains expected public API."""
        assert "ExecutionManager" in execution_v2.__all__
        assert "ExecutionResult" in execution_v2.__all__
        assert "TradeLedgerService" in execution_v2.__all__
        assert "register_execution_handlers" in execution_v2.__all__

    def test_module_has_version_attribute(self):
        """Test module has __version__ attribute for compatibility tracking."""
        assert hasattr(execution_v2, "__version__")
        assert execution_v2.__version__ == "2.0.0"


class TestRegisterExecutionHandlers:
    """Test event handler registration functionality."""

    @pytest.fixture
    def mock_container(self):
        """Create mock application container."""
        container = Mock()

        # Mock event bus
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus

        # Mock infrastructure
        mock_alpaca = Mock()
        container.infrastructure.alpaca_manager.return_value = mock_alpaca

        return container

    def test_register_execution_handlers_subscribes_to_events(self, mock_container):
        """Test that register_execution_handlers subscribes handler to events."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_execution_handlers(mock_container)

        # Verify subscribe was called with correct event type
        mock_event_bus.subscribe.assert_called_once()
        call_args = mock_event_bus.subscribe.call_args

        # First argument should be event type
        assert call_args[0][0] == "RebalancePlanned"

        # Second argument should be handler instance
        handler = call_args[0][1]
        assert handler is not None
        assert hasattr(handler, "handle_event")

    def test_register_execution_handlers_creates_handler_instance(self, mock_container):
        """Test that register_execution_handlers creates TradingExecutionHandler."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_execution_handlers(mock_container)

        # Verify handler was created and subscribed
        assert mock_event_bus.subscribe.called
        handler = mock_event_bus.subscribe.call_args[0][1]

        # Handler should have the expected interface
        assert hasattr(handler, "handle_event")
        assert hasattr(handler, "can_handle")
        assert callable(handler.handle_event)
        assert callable(handler.can_handle)

    def test_registered_handler_can_handle_rebalance_planned(self, mock_container):
        """Test that registered handler can handle RebalancePlanned events."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_execution_handlers(mock_container)

        # Get the registered handler
        handler = mock_event_bus.subscribe.call_args[0][1]

        # Verify it can handle the correct event type
        assert handler.can_handle("RebalancePlanned") is True

    def test_register_execution_handlers_gets_event_bus_from_container(self, mock_container):
        """Test that register_execution_handlers gets event bus from container."""
        # Register handlers
        register_execution_handlers(mock_container)

        # Verify event bus was obtained from container (at least once)
        assert mock_container.services.event_bus.called
        assert mock_container.services.event_bus.call_count >= 1

    def test_register_execution_handlers_multiple_calls_create_new_handlers(self, mock_container):
        """Test that calling register_execution_handlers multiple times creates new handlers."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers twice
        register_execution_handlers(mock_container)
        first_handler = mock_event_bus.subscribe.call_args[0][1]

        register_execution_handlers(mock_container)
        second_handler = mock_event_bus.subscribe.call_args[0][1]

        # Should create different handler instances
        assert first_handler is not second_handler

        # Both should be subscribed
        assert mock_event_bus.subscribe.call_count == 2
