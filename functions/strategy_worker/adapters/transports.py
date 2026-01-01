"""Business Unit: Strategy | Status: current.

Transport adapters for the strategy module.

These adapters wrap shared infrastructure clients so the strategy module
can swap transports (e.g., in-memory event bus vs. HTTP gateway) without
changing business logic. They are intentionally thin and dependency free
to make test bootstrapping easy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.events.base import BaseEvent
    from the_alchemiser.shared.events.handlers import EventHandler


class EventTransport(Protocol):
    """Protocol for event-style transports used by the strategy module."""

    def publish(self, event: BaseEvent) -> None:  # pragma: no cover - protocol
        """Publish an event to the transport."""
        ...

    def subscribe(
        self, event_type: str, handler: EventHandler
    ) -> None:  # pragma: no cover - protocol
        """Subscribe a handler to an event type."""
        ...


class HttpTransport(Protocol):
    """Minimal protocol for HTTP-style transports used by the strategy module."""

    def post(
        self, path: str, payload: dict[str, Any]
    ) -> dict[str, Any]:  # pragma: no cover - protocol
        """Post a payload to an HTTP endpoint."""
        ...


@dataclass
class StrategyTransports:
    """Bundle of transports injected into the strategy module."""

    event_bus: EventTransport
    http_client: HttpTransport | None = None


def build_strategy_transports(container: ApplicationContainer) -> StrategyTransports:
    """Build default transports from the shared container.

    Event transport defaults to the shared in-memory event bus. HTTP transport
    is optional; the strategy module rarely needs it directly, but this hook
    allows callers to supply an HTTP gateway if needed (for example, when the
    event bus is remote).
    """
    event_bus = container.services.event_bus()
    return StrategyTransports(event_bus=event_bus, http_client=None)
