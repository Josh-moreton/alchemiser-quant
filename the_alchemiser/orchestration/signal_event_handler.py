#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Event-driven signal generation handler.

Handles signal generation requests via events, eliminating direct
SignalOrchestrator method calls and enabling loose coupling.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    EventHandler,
    SignalGenerated,
    SignalGenerationRequested,
)
from the_alchemiser.shared.logging.logging_utils import get_logger


class SignalEventHandler(EventHandler):
    """Event-driven signal generation handler.
    
    Replaces direct SignalOrchestrator method calls with event-driven
    workflows for signal generation and analysis.
    """

    def __init__(self, settings: Settings, container: ApplicationContainer) -> None:
        """Initialize signal event handler.

        Args:
            settings: Application settings
            container: Application container for dependency injection
        """
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)
        self.event_bus: EventBus = container.services.event_bus()

        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register event handlers for signal workflows."""
        self.event_bus.subscribe("SignalGenerationRequested", self)
        self.logger.info("Signal event handler registered")

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can process the given event type."""
        return event_type == "SignalGenerationRequested"

    def handle_event(self, event: BaseEvent) -> None:
        """Handle signal-related events."""
        try:
            if isinstance(event, SignalGenerationRequested):
                self._handle_signal_generation_requested(event)
            else:
                self.logger.debug(f"Signal handler ignoring event type: {event.event_type}")

        except Exception as e:
            self.logger.error(
                f"Signal event handling failed: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

    def _handle_signal_generation_requested(self, event: SignalGenerationRequested) -> None:
        """Handle signal generation request event.

        Args:
            event: The signal generation request event
        """
        self.logger.info(
            f"📊 Signal generation requested: {event.analysis_mode}",
            extra={
                "correlation_id": event.correlation_id,
                "workflow_id": event.workflow_id,
            },
        )

        try:
            # Import here to avoid circular dependencies
            from the_alchemiser.orchestration.signal_orchestrator import SignalOrchestrator

            # Create signal orchestrator
            signal_orchestrator = SignalOrchestrator(self.settings, self.container)

            # Generate signals using the existing method which already emits SignalGenerated events
            result = signal_orchestrator.analyze_signals()

            if result is None:
                self.logger.error(
                    f"Signal generation failed for workflow {event.workflow_id}",
                    extra={
                        "correlation_id": event.correlation_id,
                        "workflow_id": event.workflow_id,
                    },
                )
            else:
                self.logger.info(
                    f"✅ Signal generation completed for workflow {event.workflow_id}",
                    extra={
                        "correlation_id": event.correlation_id,
                        "workflow_id": event.workflow_id,
                    },
                )

        except Exception as e:
            self.logger.error(
                f"Signal generation error for workflow {event.workflow_id}: {e}",
                extra={
                    "correlation_id": event.correlation_id,
                    "workflow_id": event.workflow_id,
                },
            )