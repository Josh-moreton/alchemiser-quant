"""Concrete observer implementations for order lifecycle events."""

from __future__ import annotations

import logging
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from the_alchemiser.domain.trading.lifecycle import OrderLifecycleEvent

logger = logging.getLogger(__name__)


class LoggingObserver:
    """Observer that logs order lifecycle events with structured information.

    This observer provides rich logging of order lifecycle transitions,
    including contextual metadata and formatted output for debugging
    and audit trail purposes.
    """

    def __init__(self, use_rich_logging: bool = True) -> None:
        """Initialize the logging observer.

        Args:
            use_rich_logging: Whether to use Rich console for formatted output

        """
        self.use_rich_logging = use_rich_logging
        self.console = Console() if use_rich_logging else None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def on_lifecycle_event(self, event: OrderLifecycleEvent) -> None:
        """Handle a lifecycle event by logging it with appropriate detail.

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
        """Render a lifecycle event using Rich console formatting.

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
            icon = "i"

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
    """Observer that collects metrics and statistics on order lifecycle events.

    Enhanced implementation tracking specific execution metrics:
    - attempt_count: Number of order placement attempts
    - time_to_fill_ms: Time from submission to fill completion
    - spread_initial/final: Initial and final spread values
    - fallback_used: Whether fallback execution strategies were used
    - volatility_pauses: Number of volatility-induced execution pauses
    """

    def __init__(self) -> None:
        """Initialize the metrics observer."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Existing metrics collection
        self._event_counts: dict[str, int] = {}
        self._transition_counts: dict[tuple[str, str], int] = {}

        # Enhanced metrics for Phase 5 requirements
        self._order_metrics: dict[str, dict[str, Any]] = {}  # order_id -> metrics
        self._attempt_counts: dict[str, int] = {}  # order_id -> attempt count
        self._submission_times: dict[str, float] = {}  # order_id -> timestamp
        self._spread_data: dict[str, dict[str, float]] = {}  # order_id -> spread info
        self._fallback_usage: dict[str, bool] = {}  # order_id -> fallback used
        self._volatility_pauses: dict[str, int] = {}  # order_id -> pause count

    def on_lifecycle_event(self, event: OrderLifecycleEvent) -> None:
        """Handle a lifecycle event by updating metrics.

        Args:
            event: The lifecycle event to process

        """
        order_id_str = str(event.order_id.value)  # Use UUID value for consistent string keys

        # Count events by type
        event_type = event.event_type.value
        self._event_counts[event_type] = self._event_counts.get(event_type, 0) + 1

        # Count state transitions
        transition_key = (
            event.previous_state.value if event.previous_state else "INITIAL",
            event.new_state.value,
        )
        self._transition_counts[transition_key] = self._transition_counts.get(transition_key, 0) + 1

        # Initialize order metrics if new order
        if order_id_str not in self._order_metrics:
            self._order_metrics[order_id_str] = {
                "order_id": order_id_str,
                "first_seen": event.timestamp.timestamp(),
                "last_updated": event.timestamp.timestamp(),
                "states_visited": [],
                "events": [],
            }
            self._attempt_counts[order_id_str] = 0
            self._volatility_pauses[order_id_str] = 0
            self._fallback_usage[order_id_str] = False

        # Update order metrics
        order_metrics = self._order_metrics[order_id_str]
        order_metrics["last_updated"] = event.timestamp.timestamp()
        order_metrics["states_visited"].append(event.new_state.value)
        order_metrics["events"].append(
            {
                "event_type": event_type,
                "timestamp": event.timestamp.timestamp(),
                "metadata": dict(event.metadata) if event.metadata else {},
            }
        )

        # Track specific metrics from metadata
        metadata = event.metadata or {}

        # Track attempt counts
        if event.new_state.value == "SUBMITTED":
            self._attempt_counts[order_id_str] += 1
            self._submission_times[order_id_str] = event.timestamp.timestamp()

            # Track initial spread if available
            if "spread_initial" in metadata and metadata["spread_initial"] is not None:
                if order_id_str not in self._spread_data:
                    self._spread_data[order_id_str] = {}
                self._spread_data[order_id_str]["initial"] = float(metadata["spread_initial"])

        # Track time to fill
        if event.new_state.value == "FILLED" and order_id_str in self._submission_times:
            fill_time = event.timestamp.timestamp()
            submission_time = self._submission_times[order_id_str]
            time_to_fill_ms = (fill_time - submission_time) * 1000
            order_metrics["time_to_fill_ms"] = time_to_fill_ms

            # Track final spread if available
            if "spread_final" in metadata and metadata["spread_final"] is not None:
                if order_id_str not in self._spread_data:
                    self._spread_data[order_id_str] = {}
                self._spread_data[order_id_str]["final"] = float(metadata["spread_final"])

        # Track fallback usage
        if metadata.get("fallback_used"):
            self._fallback_usage[order_id_str] = True

        # Track volatility pauses
        if metadata.get("volatility_pause"):
            self._volatility_pauses[order_id_str] += 1

        # Structured metrics logging
        metrics_log_data = {
            "order_id": order_id_str,
            "event_type": event_type,
            "state_transition": f"{event.previous_state} -> {event.new_state}",
            "attempt_count": self._attempt_counts.get(order_id_str, 0),
            "fallback_used": self._fallback_usage.get(order_id_str, False),
            "volatility_pauses": self._volatility_pauses.get(order_id_str, 0),
        }

        # Add time to fill for completed orders
        if "time_to_fill_ms" in order_metrics:
            metrics_log_data["time_to_fill_ms"] = order_metrics["time_to_fill_ms"]

        # Add spread data if available
        spread_data = self._spread_data.get(order_id_str, {})
        if "initial" in spread_data:
            metrics_log_data["spread_initial"] = spread_data["initial"]
        if "final" in spread_data:
            metrics_log_data["spread_final"] = spread_data["final"]

        # Log structured metrics
        self.logger.info("Order lifecycle metrics update", extra={"metrics": metrics_log_data})

        # Debug log for development
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
        """Get current event type counts.

        Returns:
            Dictionary mapping event types to occurrence counts

        """
        return dict(self._event_counts)

    def get_transition_counts(self) -> dict[tuple[str, str], int]:
        """Get current state transition counts.

        Returns:
            Dictionary mapping (from_state, to_state) tuples to counts

        """
        return dict(self._transition_counts)

    def get_order_metrics(self, order_id: str) -> dict[str, Any]:
        """Get detailed metrics for a specific order.

        Args:
            order_id: The order ID to get metrics for

        Returns:
            Dictionary containing detailed order metrics

        """
        order_metrics = self._order_metrics.get(order_id, {})
        if not order_metrics:
            return {}

        # Combine all metrics for this order
        return {
            **order_metrics,
            "attempt_count": self._attempt_counts.get(order_id, 0),
            "fallback_used": self._fallback_usage.get(order_id, False),
            "volatility_pauses": self._volatility_pauses.get(order_id, 0),
            "spread_data": self._spread_data.get(order_id, {}),
        }

    def get_execution_metrics_summary(self) -> dict[str, Any]:
        """Get summary of execution metrics across all orders.

        Returns:
            Dictionary containing aggregated execution metrics

        """
        total_orders = len(self._order_metrics)
        total_attempts = sum(self._attempt_counts.values())
        orders_with_fallback = sum(1 for used in self._fallback_usage.values() if used)
        total_volatility_pauses = sum(self._volatility_pauses.values())

        # Calculate average time to fill for completed orders
        fill_times: list[float] = []
        for metrics in self._order_metrics.values():
            time_to_fill = metrics.get("time_to_fill_ms")
            if time_to_fill is not None and isinstance(time_to_fill, (int, float)):
                fill_times.append(float(time_to_fill))

        avg_time_to_fill = sum(fill_times) / len(fill_times) if fill_times else 0.0

        return {
            "total_orders_tracked": total_orders,
            "total_submission_attempts": total_attempts,
            "average_attempts_per_order": total_attempts / total_orders if total_orders > 0 else 0,
            "orders_using_fallback": orders_with_fallback,
            "fallback_usage_rate": orders_with_fallback / total_orders if total_orders > 0 else 0,
            "total_volatility_pauses": total_volatility_pauses,
            "average_volatility_pauses_per_order": total_volatility_pauses / total_orders
            if total_orders > 0
            else 0,
            "completed_orders": len(fill_times),
            "average_time_to_fill_ms": avg_time_to_fill,
        }

    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self._event_counts.clear()
        self._transition_counts.clear()
        self._order_metrics.clear()
        self._attempt_counts.clear()
        self._submission_times.clear()
        self._spread_data.clear()
        self._fallback_usage.clear()
        self._volatility_pauses.clear()
        self.logger.info("All metrics observer data reset")
