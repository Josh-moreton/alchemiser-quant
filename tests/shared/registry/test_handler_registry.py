"""Tests for event handler registry."""

import pytest
from unittest.mock import Mock

from the_alchemiser.shared.registry.handler_registry import (
    EventHandlerRegistry, 
    HandlerRegistration
)


def test_handler_registration_creation():
    """Test creation of HandlerRegistration."""
    factory = Mock()
    registration = HandlerRegistration(
        event_type="TestEvent",
        handler_factory=factory,
        module_name="test_module", 
        priority=50,
        metadata={"test": "data"}
    )
    
    assert registration.event_type == "TestEvent"
    assert registration.handler_factory == factory
    assert registration.module_name == "test_module"
    assert registration.priority == 50
    assert registration.metadata == {"test": "data"}


def test_handler_registration_validation():
    """Test validation of HandlerRegistration."""
    factory = Mock()
    
    # Empty event_type should raise ValueError
    with pytest.raises(ValueError, match="event_type cannot be empty"):
        HandlerRegistration(
            event_type="",
            handler_factory=factory,
            module_name="test_module"
        )
    
    # Empty module_name should raise ValueError  
    with pytest.raises(ValueError, match="module_name cannot be empty"):
        HandlerRegistration(
            event_type="TestEvent",
            handler_factory=factory,
            module_name=""
        )
    
    # Negative priority should raise ValueError
    with pytest.raises(ValueError, match="priority must be non-negative"):
        HandlerRegistration(
            event_type="TestEvent", 
            handler_factory=factory,
            module_name="test_module",
            priority=-1
        )


def test_registry_registration():
    """Test handler registration in registry."""
    registry = EventHandlerRegistry()
    factory = Mock()
    
    registration = HandlerRegistration(
        event_type="TestEvent",
        handler_factory=factory,
        module_name="test_module"
    )
    
    registry.register(registration)
    
    handlers = registry.get_handlers_for_event("TestEvent")
    assert len(handlers) == 1
    assert handlers[0] == registration


def test_registry_duplicate_detection():
    """Test duplicate registration detection."""
    registry = EventHandlerRegistry()
    factory = Mock()
    
    registration1 = HandlerRegistration(
        event_type="TestEvent",
        handler_factory=factory,
        module_name="test_module"
    )
    
    registration2 = HandlerRegistration(
        event_type="TestEvent", 
        handler_factory=factory,
        module_name="test_module"  # Same module and event
    )
    
    registry.register(registration1)
    
    with pytest.raises(ValueError, match="already registered"):
        registry.register(registration2)


def test_registry_priority_ordering():
    """Test priority ordering in registry."""
    registry = EventHandlerRegistry()
    factory = Mock()
    
    # Register handlers with different priorities
    high_priority = HandlerRegistration(
        event_type="TestEvent",
        handler_factory=factory,
        module_name="high_module",
        priority=10
    )
    
    low_priority = HandlerRegistration(
        event_type="TestEvent",
        handler_factory=factory, 
        module_name="low_module",
        priority=100
    )
    
    # Register in reverse priority order
    registry.register(low_priority)
    registry.register(high_priority)
    
    handlers = registry.get_handlers_for_event("TestEvent")
    assert len(handlers) == 2
    assert handlers[0] == high_priority  # Lower priority number = higher priority
    assert handlers[1] == low_priority


def test_registry_convenience_method():
    """Test convenience registration method."""
    registry = EventHandlerRegistry()
    factory = Mock()
    
    registry.register_handler(
        event_type="TestEvent",
        handler_factory=factory,
        module_name="test_module",
        priority=50,
        metadata={"test": "data"}
    )
    
    handlers = registry.get_handlers_for_event("TestEvent")
    assert len(handlers) == 1
    
    registration = handlers[0]
    assert registration.event_type == "TestEvent"
    assert registration.module_name == "test_module"
    assert registration.priority == 50
    assert registration.metadata == {"test": "data"}


def test_registry_get_methods():
    """Test registry getter methods."""
    registry = EventHandlerRegistry()
    factory = Mock()
    
    reg1 = HandlerRegistration("Event1", factory, "module1")
    reg2 = HandlerRegistration("Event2", factory, "module1") 
    reg3 = HandlerRegistration("Event1", factory, "module2")
    
    registry.register(reg1)
    registry.register(reg2)
    registry.register(reg3)
    
    # Test get_handlers_for_event
    event1_handlers = registry.get_handlers_for_event("Event1")
    assert len(event1_handlers) == 2
    assert reg1 in event1_handlers
    assert reg3 in event1_handlers
    
    # Test get_handlers_for_module
    module1_handlers = registry.get_handlers_for_module("module1")
    assert len(module1_handlers) == 2
    assert reg1 in module1_handlers
    assert reg2 in module1_handlers
    
    # Test get_supported_events
    supported_events = registry.get_supported_events()
    assert supported_events == {"Event1", "Event2"}
    
    # Test get_all_registrations
    all_registrations = registry.get_all_registrations()
    assert len(all_registrations) == 3
    assert reg1 in all_registrations
    assert reg2 in all_registrations
    assert reg3 in all_registrations


def test_registry_clear():
    """Test registry clear functionality."""
    registry = EventHandlerRegistry()
    factory = Mock()
    
    registration = HandlerRegistration("TestEvent", factory, "test_module")
    registry.register(registration)
    
    assert len(registry.get_all_registrations()) == 1
    
    registry.clear()
    
    assert len(registry.get_all_registrations()) == 0
    assert len(registry.get_supported_events()) == 0