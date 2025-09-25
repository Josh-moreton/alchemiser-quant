"""Tests for registry integration with orchestrator."""

import pytest
from unittest.mock import Mock, MagicMock

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.registry.handler_registry import EventHandlerRegistry


def test_container_provides_registry():
    """Test that the DI container provides the handler registry."""
    container = ApplicationContainer.create_for_testing()
    
    # The registry should be available from the container
    registry = container.services.event_handler_registry()
    assert isinstance(registry, EventHandlerRegistry)


def test_module_registration_functions():
    """Test that module registration functions work with registry."""
    container = ApplicationContainer.create_for_testing()
    registry = EventHandlerRegistry()
    
    # Import and test registration functions
    from the_alchemiser.strategy_v2 import register_strategy_handlers
    from the_alchemiser.portfolio_v2 import register_portfolio_handlers
    from the_alchemiser.execution_v2 import register_execution_handlers
    
    # Register handlers from each module
    register_strategy_handlers(container, registry)
    register_portfolio_handlers(container, registry)
    register_execution_handlers(container, registry)
    
    # Verify registrations
    all_registrations = registry.get_all_registrations()
    assert len(all_registrations) > 0
    
    # Check expected event types are supported
    supported_events = registry.get_supported_events()
    expected_events = {"StartupEvent", "WorkflowStarted", "SignalGenerated", "RebalancePlanned"}
    assert expected_events.issubset(supported_events)
    
    # Check modules are registered
    strategy_handlers = registry.get_handlers_for_module("strategy_v2")
    portfolio_handlers = registry.get_handlers_for_module("portfolio_v2")
    execution_handlers = registry.get_handlers_for_module("execution_v2")
    
    assert len(strategy_handlers) > 0
    assert len(portfolio_handlers) > 0
    assert len(execution_handlers) > 0


def test_orchestrator_uses_registry(monkeypatch):
    """Test that EventDrivenOrchestrator uses the registry for handler initialization."""
    # Create a mock container with registry
    container = Mock()
    event_bus_mock = Mock()
    registry_mock = Mock()
    
    container.services.event_bus.return_value = event_bus_mock
    container.services.event_handler_registry.return_value = registry_mock
    
    # Mock registry to return some test registrations
    mock_handler = Mock()
    mock_handler.can_handle.return_value = True
    
    test_registration = Mock()
    test_registration.event_type = "TestEvent"
    test_registration.module_name = "strategy_v2"
    test_registration.priority = 100
    test_registration.handler_factory.return_value = mock_handler
    
    registry_mock.get_all_registrations.return_value = [test_registration]
    
    # Import and create orchestrator
    from the_alchemiser.orchestration.event_driven_orchestrator import EventDrivenOrchestrator
    
    # Mock the logger to avoid actual logging during test
    with monkeypatch.context() as m:
        mock_logger = Mock()
        m.setattr("the_alchemiser.orchestration.event_driven_orchestrator.get_logger", lambda x: mock_logger)
        
        orchestrator = EventDrivenOrchestrator(container)
        
        # Verify registry was used
        registry_mock.get_all_registrations.assert_called()
        
        # Verify handler was created using factory
        test_registration.handler_factory.assert_called()
        
        # Verify event bus subscription occurred
        event_bus_mock.subscribe.assert_called()


@pytest.fixture
def sample_container():
    """Create a sample container for testing."""
    return ApplicationContainer.create_for_testing()


def test_system_builds_registry(sample_container, monkeypatch):
    """Test that TradingSystem builds the registry during initialization."""
    # Mock the registration functions to avoid actual handler creation
    mock_strategy_reg = Mock()
    mock_portfolio_reg = Mock()
    mock_execution_reg = Mock()
    
    with monkeypatch.context() as m:
        m.setattr("the_alchemiser.strategy_v2.register_strategy_handlers", mock_strategy_reg)
        m.setattr("the_alchemiser.portfolio_v2.register_portfolio_handlers", mock_portfolio_reg)
        m.setattr("the_alchemiser.execution_v2.register_execution_handlers", mock_execution_reg)
        
        # Mock EventDrivenOrchestrator import within system.py
        mock_orchestrator_class = Mock()
        m.setattr(
            "the_alchemiser.orchestration.event_driven_orchestrator.EventDrivenOrchestrator", 
            mock_orchestrator_class
        )
        
        from the_alchemiser.orchestration.system import TradingSystem
        
        # Create system (this should trigger registry building)
        system = TradingSystem()
        
        # Verify registration functions were called
        mock_strategy_reg.assert_called_once()
        mock_portfolio_reg.assert_called_once()
        mock_execution_reg.assert_called_once()
        
        # Verify all were called with container and registry
        for mock_reg_func in [mock_strategy_reg, mock_portfolio_reg, mock_execution_reg]:
            args, kwargs = mock_reg_func.call_args
            assert len(args) == 2  # container and registry
            assert args[0] is not None  # container
            assert args[1] is not None  # registry