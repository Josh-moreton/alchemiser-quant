"""Business Unit: notifications | Status: current.

Notifications V2 Module - Event-Driven Email Service.

This module provides event-driven email notification services that can be deployed
independently as a Lambda function. It consumes notification events from the
event bus and sends appropriate emails.

Public API:
    register_notification_handlers: Register event handlers for notifications
    NotificationService: Core service for handling notification events
    StrategyPerformanceReportService: Service for generating CSV performance reports
    generate_performance_report_url: Convenience function for report generation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from .service import NotificationService
from .strategy_report_service import (
    StrategyPerformanceReportService,
    generate_performance_report_url,
)


def register_notification_handlers(container: ApplicationContainer) -> None:
    """Register notification event handlers with the event bus.

    Args:
        container: Application container for dependency injection.
            Must be fully initialized with services.event_bus available.

    Returns:
        None

    Raises:
        AttributeError: If container is not properly initialized
        Exception: If service initialization or handler registration fails

    """
    notification_service = NotificationService(container)
    notification_service.register_handlers()


# Public API exports
__all__ = [
    "NotificationService",
    "StrategyPerformanceReportService",
    "generate_performance_report_url",
    "register_notification_handlers",
]

# Version for compatibility tracking
__version__ = "2.0.0"
