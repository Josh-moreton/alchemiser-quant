"""Tests for strategy handler registration."""

import pytest
from unittest.mock import Mock, MagicMock

from the_alchemiser.shared.registry.handler_registry import EventHandlerRegistry
from the_alchemiser.strategy_v2 import register_strategy_handlers


class TestStrategyHandlerRegistration:
    """Test strategy handler registration functionality."""

    def test_register_strategy_handlers_creates_registrations(self):
        """Test that handler registration creates proper registrations."""
        # Mock dependencies
        container = Mock()
        registry = EventHandlerRegistry()
        
        # Register handlers
        register_strategy_handlers(container, registry)
        
        # Check that handlers were registered
        startup_handlers = registry.get_handlers_for_event("StartupEvent")
        workflow_handlers = registry.get_handlers_for_event("WorkflowStarted")
        
        assert len(startup_handlers) == 1
        assert len(workflow_handlers) == 1
        
        # Check registration details
        startup_reg = startup_handlers[0]
        assert startup_reg.event_type == "StartupEvent"
        assert startup_reg.module_name == "strategy_v2"
        assert startup_reg.priority == 100
        assert "description" in startup_reg.metadata
        
        workflow_reg = workflow_handlers[0]
        assert workflow_reg.event_type == "WorkflowStarted"
        assert workflow_reg.module_name == "strategy_v2"
        assert workflow_reg.priority == 100

    def test_handler_factory_creates_signal_generation_handler(self):
        """Test that handler factory creates proper handler instances."""
        container = Mock()
        registry = EventHandlerRegistry()
        
        # Register handlers
        register_strategy_handlers(container, registry)
        
        # Get a handler registration
        startup_handlers = registry.get_handlers_for_event("StartupEvent")
        handler_reg = startup_handlers[0]
        
        # Create handler using factory
        handler = handler_reg.handler_factory()
        
        # Check handler properties
        assert hasattr(handler, "handle_event")
        assert hasattr(handler, "can_handle")
        assert handler.container == container

    def test_handler_can_handle_correct_events(self):
        """Test that created handlers can handle the correct event types."""
        container = Mock()
        registry = EventHandlerRegistry()
        
        # Register handlers
        register_strategy_handlers(container, registry)
        
        # Create handler
        startup_handlers = registry.get_handlers_for_event("StartupEvent")
        handler = startup_handlers[0].handler_factory()
        
        # Test event handling capability
        assert handler.can_handle("StartupEvent")
        assert handler.can_handle("WorkflowStarted")
        assert not handler.can_handle("SomeOtherEvent")

    def test_multiple_registrations_no_duplicates(self):
        """Test that multiple registrations don't create duplicates."""
        container = Mock()
        registry = EventHandlerRegistry()
        
        # Register handlers multiple times
        register_strategy_handlers(container, registry)
        
        # Second registration should fail due to duplicate check
        with pytest.raises(ValueError, match="already registered"):
            register_strategy_handlers(container, registry)

    def test_registry_supports_strategy_module(self):
        """Test that registry properly tracks strategy module handlers."""
        container = Mock()
        registry = EventHandlerRegistry()
        
        # Register handlers
        register_strategy_handlers(container, registry)
        
        # Check module-specific handlers
        strategy_handlers = registry.get_handlers_for_module("strategy_v2")
        
        assert len(strategy_handlers) == 2  # StartupEvent and WorkflowStarted
        
        # Check that all handlers are from strategy_v2 module
        for handler_reg in strategy_handlers:
            assert handler_reg.module_name == "strategy_v2"
            assert handler_reg.metadata.get("handler_class") == "SignalGenerationHandler"