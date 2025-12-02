"""Business Unit: reporting | Status: current.

PDF report generation module for The Alchemiser.

This module handles PDF report generation from account snapshots,
including metrics computation and rendering.

Architecture Note:
    This module follows the lightweight pattern - it avoids importing
    ApplicationContainer to prevent pulling in heavy dependencies (pandas, numpy)
    that are not needed for PDF report generation.

Public API (Event-Driven):
    - register_reporting_handlers: Event handler registration (lightweight mode)

FastAPI Surface:
    - create_app: Factory function for FastAPI application
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.reporting.adapters.transports import EventTransport


def register_reporting_handlers(event_bus: EventTransport | None = None) -> None:
    """Register reporting event handlers with the event bus.

    Note: The reporting module is primarily request-driven (generates reports
    on demand via API calls or Lambda invocations). It does not subscribe to
    events by default, but this function is provided for consistency with
    other modules and future extensibility.

    Unlike other modules, this function does NOT take an ApplicationContainer
    to keep dependencies lightweight.

    Args:
        event_bus: Optional event transport for handler registration.
            If provided, can be used to subscribe to events that trigger
            report generation (e.g., WorkflowCompleted for auto-reports).

    Example:
        >>> from the_alchemiser.shared.events.bus import EventBus
        >>> event_bus = EventBus()
        >>> register_reporting_handlers(event_bus)

    """
    from the_alchemiser.shared.logging import get_logger

    logger = get_logger(__name__)

    logger.info(
        "Registering reporting event handlers (lightweight mode)",
        extra={"module": "reporting", "component": "register_reporting_handlers"},
    )

    # The reporting module is request-driven - it generates reports on demand.
    # No event subscriptions are registered by default.
    # Future: Could subscribe to WorkflowCompleted for auto-report generation.

    if event_bus is not None:
        logger.debug(
            "Event bus provided but no subscriptions configured",
            extra={"module": "reporting", "note": "request-driven module"},
        )

    logger.info(
        "Reporting handlers registered successfully (no subscriptions - request-driven)",
        extra={"module": "reporting"},
    )


__all__ = ["register_reporting_handlers"]
