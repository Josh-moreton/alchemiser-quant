"""Concrete observer implementations for order lifecycle events."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from the_alchemiser.domain.trading.lifecycle import OrderLifecycleEvent

logger = logging.getLogger(__name__)


class LoggingObserver:
    """
    Observer that logs order lifecycle events with structured information.

    This observer provides rich logging of order lifecycle transitions,
    including contextual metadata and formatted output for debugging
    and audit trail purposes.
    """

    def __init__(self, use_rich_logging: bool = True) -> None:
        """
        Initialize the logging observer.

        Args:
            use_rich_logging: Whether to use Rich console for formatted output
        """
        self.use_rich_logging = use_rich_logging
        self.console = Console() if use_rich_logging else None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def on_lifecycle_event(self, event: OrderLifecycleEvent) -> None:
        """
        Handle a lifecycle event by logging it with appropriate detail.

        Args:
            event: The lifecycle event to log
        """
        # Build structured log data
        log_data = {
            "order_id": str(event.order_id),
            "previous_state": event.previous_state.value if event.previous_state else None,
            "new_state": event.new_state.value,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "metadata": dict(event.metadata) if event.metadata else {},
        }

        # Determine log level based on event type
        if event.is_error_transition():
            log_level = logging.WARNING
            log_message = f"Order {event.order_id} error transition: {event.previous_state} -> {event.new_state}"
        elif event.is_terminal_transition():
            log_level = logging.INFO
            log_message = (
                f"Order {event.order_id} completed: {event.previous_state} -> {event.new_state}"
            )
        else:
            log_level = logging.DEBUG
            log_message = (
                f"Order {event.order_id} transition: {event.previous_state} -> {event.new_state}"
            )

        # Log with structured data
        self.logger.log(
            log_level,
            log_message,
            extra={"lifecycle_event": log_data},
        )

        # Rich console output for important events
        if self.use_rich_logging and self.console and log_level >= logging.INFO:
            self._render_rich_event(event)

    def _render_rich_event(self, event: OrderLifecycleEvent) -> None:
        """
        Render a lifecycle event using Rich console formatting.

        Args:
            event: Event to render
        """
        if not self.console:
            return

        # Choose color based on event type
        if event.is_success_transition():
            color = "green"
            icon = "✅"
        elif event.is_error_transition():
            color = "red"
            icon = "❌"
        else:
            color = "blue"
            icon = "ℹ️"

        # Create summary table
        table = Table(show_header=False, padding=(0, 1))
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row("Order ID", str(event.order_id))
        table.add_row("Transition", f"{event.previous_state} → {event.new_state}")
        table.add_row("Event Type", event.event_type.value)
        table.add_row("Timestamp", event.timestamp.strftime("%H:%M:%S UTC"))

        # Add metadata if present
        if event.metadata:
            for key, value in event.metadata.items():
                table.add_row(f"  {key}", str(value))

        # Create panel with appropriate styling
        panel = Panel(
            table,
            title=f"{icon} Order Lifecycle Event",
            border_style=color,
            padding=(1, 2),
        )

        self.console.print(panel)


class MetricsObserver:
    """
    Observer that collects metrics and statistics on order lifecycle events.

    This is a placeholder implementation that can be extended to integrate
    with metrics collection systems like Prometheus, CloudWatch, etc.
    """

    def __init__(self) -> None:
        """Initialize the metrics observer."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Placeholder for metrics collection
        self._event_counts: dict[str, int] = {}
        self._transition_counts: dict[tuple[str, str], int] = {}

    def on_lifecycle_event(self, event: OrderLifecycleEvent) -> None:
        """
        Handle a lifecycle event by updating metrics.

        Args:
            event: The lifecycle event to process
        """
        # Count events by type
        event_type = event.event_type.value
        self._event_counts[event_type] = self._event_counts.get(event_type, 0) + 1

        # Count state transitions
        transition_key = (
            event.previous_state.value if event.previous_state else "INITIAL",
            event.new_state.value,
        )
        self._transition_counts[transition_key] = self._transition_counts.get(transition_key, 0) + 1

        # Log metrics update (placeholder)
        self.logger.debug(
            "Updated metrics for order lifecycle event: %s (%s -> %s)",
            event_type,
            event.previous_state,
            event.new_state,
        )

        # TODO: Integrate with actual metrics system
        # Examples:
        # - prometheus_client.Counter for event counts
        # - CloudWatch custom metrics
        # - StatsD for real-time metrics
        # - Database storage for historical analysis

    def get_event_counts(self) -> dict[str, int]:
        """
        Get current event type counts.

        Returns:
            Dictionary mapping event types to occurrence counts
        """
        return dict(self._event_counts)

    def get_transition_counts(self) -> dict[tuple[str, str], int]:
        """
        Get current state transition counts.

        Returns:
            Dictionary mapping (from_state, to_state) tuples to counts
        """
        return dict(self._transition_counts)

    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self._event_counts.clear()
        self._transition_counts.clear()
        self.logger.info("Metrics observer counters reset")
