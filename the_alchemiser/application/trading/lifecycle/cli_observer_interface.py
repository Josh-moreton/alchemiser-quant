"""Business Unit: order execution/placement; Status: current.

CLI Observer Interface for Lifecycle Events.

Provides a clean Protocol interface for CLI components to subscribe to lifecycle events
without introducing console printing or rich formatting into the core trading system.
"""

from __future__ import annotations

from typing import Any, Protocol

from the_alchemiser.domain.trading.lifecycle import OrderLifecycleEvent


class CLILifecycleObserver(Protocol):
    """Protocol interface for CLI components to observe lifecycle events.

    This protocol allows CLI components to subscribe to lifecycle events
    without coupling the core trading system to any specific UI framework
    or output mechanism.
    """

    def on_order_submitted(self, order_id: str, metadata: dict[str, Any]) -> None:
        """Handle order submission event.

        Args:
            order_id: The unique order identifier
            metadata: Event metadata containing submission details

        """
        ...

    def on_order_filled(self, order_id: str, metadata: dict[str, Any]) -> None:
        """Handle order fill completion event.

        Args:
            order_id: The unique order identifier
            metadata: Event metadata containing fill details

        """
        ...

    def on_order_rejected(self, order_id: str, metadata: dict[str, Any]) -> None:
        """Handle order rejection event.

        Args:
            order_id: The unique order identifier
            metadata: Event metadata containing rejection details

        """
        ...

    def on_order_timeout(self, order_id: str, metadata: dict[str, Any]) -> None:
        """Handle order timeout event.

        Args:
            order_id: The unique order identifier
            metadata: Event metadata containing timeout details

        """
        ...

    def on_order_partial_fill(self, order_id: str, metadata: dict[str, Any]) -> None:
        """Handle order partial fill event.

        Args:
            order_id: The unique order identifier
            metadata: Event metadata containing partial fill details

        """
        ...


class CLIObserverAdapter:
    """Adapter that bridges domain lifecycle events to CLI observer protocol.

    This adapter subscribes to the domain lifecycle event system and translates
    events to CLI-specific method calls, enabling loose coupling between
    the core domain and CLI presentation concerns.
    """

    def __init__(self, cli_observer: CLILifecycleObserver) -> None:
        """Initialize the adapter with a CLI observer.

        Args:
            cli_observer: CLI component implementing CLILifecycleObserver protocol

        """
        self.cli_observer = cli_observer

    def on_lifecycle_event(self, event: OrderLifecycleEvent) -> None:
        """Translate domain lifecycle events to CLI observer calls.

        Args:
            event: Domain lifecycle event to translate

        """
        # Extract the actual UUID string from the OrderId
        order_id_str = str(event.order_id.value)  # Get the UUID value, not the OrderId repr
        metadata = dict(event.metadata) if event.metadata else {}

        # Add common event data to metadata
        event_metadata = {
            **metadata,
            "event_type": event.event_type.value,
            "previous_state": event.previous_state.value if event.previous_state else None,
            "new_state": event.new_state.value,
            "timestamp": event.timestamp.isoformat(),
        }

        # Route to appropriate CLI observer method based on state/event type
        if event.new_state.value == "SUBMITTED":
            self.cli_observer.on_order_submitted(order_id_str, event_metadata)
        elif event.new_state.value == "FILLED":
            self.cli_observer.on_order_filled(order_id_str, event_metadata)
        elif event.new_state.value == "REJECTED":
            self.cli_observer.on_order_rejected(order_id_str, event_metadata)
        elif event.event_type.value == "TIMEOUT":
            self.cli_observer.on_order_timeout(order_id_str, event_metadata)
        elif event.new_state.value == "PARTIALLY_FILLED":
            self.cli_observer.on_order_partial_fill(order_id_str, event_metadata)
