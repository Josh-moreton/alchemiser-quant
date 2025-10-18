"""Business Unit: portfolio | Status: current

Test portfolio_v2 module imports and public API.

Tests that the module's public API exports work correctly and
event handler registration functions as expected.
"""

from unittest.mock import Mock

import pytest

from the_alchemiser import portfolio_v2
from the_alchemiser.portfolio_v2 import (
    PortfolioServiceV2,
    RebalancePlanCalculator,
    register_portfolio_handlers,
)


class TestPortfolioV2ModuleImports:
    """Test portfolio_v2 module imports and exports."""

    def test_import_portfolio_service_v2(self):
        """Test importing PortfolioServiceV2 from module."""
        assert PortfolioServiceV2 is not None
        assert hasattr(PortfolioServiceV2, "__init__")

    def test_import_rebalance_plan_calculator(self):
        """Test importing RebalancePlanCalculator from module."""
        assert RebalancePlanCalculator is not None
        assert hasattr(RebalancePlanCalculator, "__init__")

    def test_import_register_portfolio_handlers(self):
        """Test importing register_portfolio_handlers function."""
        from the_alchemiser.portfolio_v2 import register_portfolio_handlers

        assert register_portfolio_handlers is not None
        assert callable(register_portfolio_handlers)

    def test_getattr_portfolio_service_v2(self):
        """Test __getattr__ for PortfolioServiceV2."""
        service_class = portfolio_v2.PortfolioServiceV2
        assert service_class is not None

    def test_getattr_rebalance_plan_calculator(self):
        """Test __getattr__ for RebalancePlanCalculator."""
        calculator_class = portfolio_v2.RebalancePlanCalculator
        assert calculator_class is not None

    def test_getattr_invalid_attribute_raises_error(self):
        """Test __getattr__ raises AttributeError for invalid attribute."""
        with pytest.raises(AttributeError) as exc_info:
            portfolio_v2.NonExistentClass

        assert "NonExistentClass" in str(exc_info.value)

    def test_all_contains_expected_exports(self):
        """Test __all__ contains expected public API."""
        assert "PortfolioServiceV2" in portfolio_v2.__all__
        assert "RebalancePlanCalculator" in portfolio_v2.__all__
        assert "register_portfolio_handlers" in portfolio_v2.__all__


class TestRegisterPortfolioHandlers:
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

    def test_register_portfolio_handlers_subscribes_to_events(self, mock_container):
        """Test that register_portfolio_handlers subscribes handler to events."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_portfolio_handlers(mock_container)

        # Verify subscribe was called with correct event type
        mock_event_bus.subscribe.assert_called_once()
        call_args = mock_event_bus.subscribe.call_args

        # First argument should be event type
        assert call_args[0][0] == "SignalGenerated"

        # Second argument should be handler instance
        handler = call_args[0][1]
        assert handler is not None
        assert hasattr(handler, "handle_event")

    def test_register_portfolio_handlers_creates_handler_instance(self, mock_container):
        """Test that register_portfolio_handlers creates PortfolioAnalysisHandler."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_portfolio_handlers(mock_container)

        # Verify handler was created and subscribed
        assert mock_event_bus.subscribe.called
        handler = mock_event_bus.subscribe.call_args[0][1]

        # Handler should have the expected interface
        assert hasattr(handler, "handle_event")
        assert hasattr(handler, "can_handle")
        assert callable(handler.handle_event)
        assert callable(handler.can_handle)

    def test_registered_handler_can_handle_signal_generated(self, mock_container):
        """Test that registered handler can handle SignalGenerated events."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers
        register_portfolio_handlers(mock_container)

        # Get the registered handler
        handler = mock_event_bus.subscribe.call_args[0][1]

        # Verify it can handle the correct event type
        assert handler.can_handle("SignalGenerated") is True

    def test_register_portfolio_handlers_gets_event_bus_from_container(self, mock_container):
        """Test that register_portfolio_handlers gets event bus from container."""
        # Register handlers
        register_portfolio_handlers(mock_container)

        # Verify event bus was obtained from container (at least once)
        assert mock_container.services.event_bus.called
        assert mock_container.services.event_bus.call_count >= 1

    def test_register_portfolio_handlers_multiple_calls_create_new_handlers(self, mock_container):
        """Test that calling register_portfolio_handlers multiple times creates new handlers."""
        mock_event_bus = mock_container.services.event_bus.return_value

        # Register handlers twice
        register_portfolio_handlers(mock_container)
        first_handler = mock_event_bus.subscribe.call_args[0][1]

        register_portfolio_handlers(mock_container)
        second_handler = mock_event_bus.subscribe.call_args[0][1]

        # Should create different handler instances
        assert first_handler is not second_handler

        # Both should be subscribed
        assert mock_event_bus.subscribe.call_count == 2
