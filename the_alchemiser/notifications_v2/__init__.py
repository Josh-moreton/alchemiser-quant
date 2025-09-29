"""Business Unit: notifications | Status: current.

Notifications V2 Module - Event-Driven Email Service.

This module provides event-driven email notification services that can be deployed
independently as a Lambda function. It consumes notification events from the 
event bus and sends appropriate emails.

Public API:
    register_notification_handlers: Register event handlers for notifications
    NotificationService: Core service for handling notification events
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from .service import NotificationService


def register_notification_handlers(container: ApplicationContainer) -> None:
    """Register notification event handlers with the event bus.
    
    Args:
        container: Application container for dependency injection
    """
    notification_service = NotificationService(container)
    notification_service.register_handlers()


# Public API exports
__all__ = [
    "register_notification_handlers",
    "NotificationService",
]