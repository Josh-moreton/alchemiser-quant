#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Global test configuration and fixtures.

Provides common test fixtures and configuration for the entire test suite,
including event-driven test harness and mock utilities.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.handlers import EventHandler


@pytest.fixture
def test_timestamp() -> datetime:
    """Provide a fixed timestamp for deterministic testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def test_correlation_id() -> str:
    """Provide a fixed correlation ID for deterministic testing."""
    return "test-correlation-12345"


@pytest.fixture
def event_bus() -> EventBus:
    """Provide a fresh EventBus instance for each test."""
    return EventBus()


@pytest.fixture
def mock_event_handler() -> Mock:
    """Provide a mock event handler for testing."""
    handler = Mock(spec=EventHandler)
    handler.can_handle.return_value = True
    return handler


@pytest.fixture
def test_events_list() -> list[BaseEvent]:
    """Provide a list to collect events for testing."""
    return []


class EventRecorder(EventHandler):
    """Event handler that records all events for testing purposes."""
    
    def __init__(self) -> None:
        """Initialize the event recorder."""
        self.events: list[BaseEvent] = []
        self.event_counts: dict[str, int] = {}
    
    def handle_event(self, event: BaseEvent) -> None:
        """Record an event."""
        self.events.append(event)
        self.event_counts[event.event_type] = self.event_counts.get(event.event_type, 0) + 1
    
    def can_handle(self, event_type: str) -> bool:
        """Handle all event types."""
        return True
    
    def clear(self) -> None:
        """Clear all recorded events."""
        self.events.clear()
        self.event_counts.clear()
    
    def get_events_by_type(self, event_type: str) -> list[BaseEvent]:
        """Get all events of a specific type."""
        return [event for event in self.events if event.event_type == event_type]


@pytest.fixture
def event_recorder(event_bus: EventBus) -> EventRecorder:
    """Provide an event recorder subscribed to the event bus."""
    recorder = EventRecorder()
    event_bus.subscribe_global(recorder)
    return recorder


@pytest.fixture
def repository_root() -> Path:
    """Provide the repository root path."""
    return Path(__file__).parent.parent


@pytest.fixture
def clj_strategy_files(repository_root: Path) -> list[Path]:
    """Discover all CLJ strategy files in the repository."""
    clj_files = list(repository_root.glob("*.clj"))
    # Sort for deterministic test ordering
    return sorted(clj_files)


@pytest.fixture
def test_snapshots_dir(repository_root: Path) -> Path:
    """Provide the directory for test snapshots."""
    snapshots_dir = repository_root / "tests" / "snapshots"
    snapshots_dir.mkdir(exist_ok=True)
    return snapshots_dir


@pytest.fixture
def virtual_clock():
    """Provide a virtual clock for deterministic time-based testing."""
    
    class VirtualClock:
        def __init__(self, start_time: datetime | None = None) -> None:
            self.current_time = start_time or datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        
        def now(self) -> datetime:
            """Get current virtual time."""
            return self.current_time
        
        def advance(self, seconds: int) -> None:
            """Advance virtual time by specified seconds."""
            from datetime import timedelta
            self.current_time += timedelta(seconds=seconds)
        
        def set_time(self, new_time: datetime) -> None:
            """Set virtual time to specific datetime."""
            self.current_time = new_time
    
    return VirtualClock()


# Seed for deterministic randomization in property-based tests
@pytest.fixture
def random_seed() -> int:
    """Provide a fixed random seed for deterministic testing."""
    return 42


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment between tests to prevent cross-test contamination."""
    # This fixture runs automatically before each test
    yield
    # Cleanup code would go here if needed