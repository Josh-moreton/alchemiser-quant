"""Business Unit: Reporting | Status: current.

Transport adapters for the reporting module.

These adapters wrap shared infrastructure clients so the reporting module
can swap transports (e.g., in-memory event bus vs. HTTP gateway) without
changing business logic. They are intentionally thin and dependency free
to make test bootstrapping easy.

Architecture Note:
    This module avoids importing ApplicationContainer to keep dependencies minimal.
    The reporting module creates a lightweight EventBus directly rather than
    pulling in heavy dependencies (pandas, numpy) via the container.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from the_alchemiser.shared.events.base import BaseEvent
    from the_alchemiser.shared.events.handlers import EventHandler


class EventTransport(Protocol):
    """Protocol for event-style transports used by the reporting module."""

    def publish(self, event: BaseEvent) -> None:  # pragma: no cover - protocol
        """Publish an event to the transport."""
        ...

    def subscribe(
        self, event_type: str, handler: EventHandler
    ) -> None:  # pragma: no cover - protocol
        """Subscribe a handler to an event type."""
        ...


class HttpTransport(Protocol):
    """Minimal protocol for HTTP-style transports used by the reporting module."""

    def post(
        self, path: str, payload: dict[str, Any]
    ) -> dict[str, Any]:  # pragma: no cover - protocol
        """Post a payload to an HTTP endpoint."""
        ...


@dataclass
class ReportingTransports:
    """Bundle of transports injected into the reporting module."""

    event_bus: EventTransport
    http_client: HttpTransport | None = None


def build_reporting_transports_lightweight() -> ReportingTransports:
    """Build transports using a lightweight EventBus (no ApplicationContainer).

    This function creates a standalone EventBus without going through
    ApplicationContainer, avoiding heavy dependencies like pandas/numpy
    that are not needed for PDF report generation.

    Returns:
        ReportingTransports bundle with lightweight event bus.

    """
    from the_alchemiser.shared.events.bus import EventBus

    event_bus = EventBus()
    return ReportingTransports(event_bus=event_bus, http_client=None)
