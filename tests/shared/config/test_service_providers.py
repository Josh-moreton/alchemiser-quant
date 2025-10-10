#!/usr/bin/env python3
"""Tests for ServiceProviders dependency injection container.

Business Unit: shared | Status: current

Tests DI configuration for service layer components.
"""

from __future__ import annotations

import pytest
from dependency_injector import containers, providers

from the_alchemiser.shared.config.service_providers import ServiceProviders
from the_alchemiser.shared.events.bus import EventBus


def test_service_providers_has_dependencies_containers() -> None:
    """Test that ServiceProviders declares infrastructure and config dependencies."""
    container = ServiceProviders()

    # Should have DependenciesContainer attributes
    assert hasattr(container, "infrastructure")
    assert hasattr(container, "config")

    # Should be DependenciesContainer types
    assert isinstance(container.infrastructure, providers.DependenciesContainer)
    assert isinstance(container.config, providers.DependenciesContainer)


def test_service_providers_event_bus_is_singleton() -> None:
    """Test that event_bus provider is singleton."""
    container = ServiceProviders()

    # Get two instances
    bus1 = container.event_bus()
    bus2 = container.event_bus()

    # Should be same instance (singleton)
    assert bus1 is bus2
    assert isinstance(bus1, EventBus)


def test_service_providers_event_bus_type() -> None:
    """Test that event_bus returns correct type."""
    container = ServiceProviders()
    bus = container.event_bus()

    assert isinstance(bus, EventBus)
    assert hasattr(bus, "publish")
    assert hasattr(bus, "subscribe")


def test_service_providers_can_be_composed() -> None:
    """Test that ServiceProviders can be composed in parent container."""
    # Create mock parent dependencies
    mock_infrastructure = containers.DynamicContainer()
    mock_config = containers.DynamicContainer()

    # Create container and override dependencies
    container = ServiceProviders()
    container.infrastructure.override(mock_infrastructure)
    container.config.override(mock_config)

    # Should not raise
    bus = container.event_bus()
    assert isinstance(bus, EventBus)


def test_service_providers_multiple_containers_independent() -> None:
    """Test that multiple ServiceProviders containers are independent."""
    container1 = ServiceProviders()
    container2 = ServiceProviders()

    bus1 = container1.event_bus()
    bus2 = container2.event_bus()

    # Different containers = different singletons
    assert bus1 is not bus2


def test_service_providers_event_bus_has_required_methods() -> None:
    """Test that EventBus has required pub/sub methods."""
    container = ServiceProviders()
    bus = container.event_bus()

    # Check required methods for event-driven architecture
    assert callable(bus.publish)
    assert callable(bus.subscribe)
    assert callable(bus.unsubscribe)
    assert callable(bus.get_handler_count)
    assert callable(bus.get_event_count)


def test_service_providers_container_inheritance() -> None:
    """Test that ServiceProviders inherits from DeclarativeContainer."""
    container = ServiceProviders()
    assert isinstance(container, containers.DeclarativeContainer)
