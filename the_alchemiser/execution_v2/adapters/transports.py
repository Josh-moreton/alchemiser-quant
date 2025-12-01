"""Business Unit: Execution | Status: current.

Transport adapters for the execution module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from the_alchemiser.shared.events.base import BaseEvent
    from the_alchemiser.shared.events.handlers import EventHandler


class EventTransport(Protocol):
    """Protocol for event-style transports used by the execution module."""

    def publish(self, event: BaseEvent) -> None:  # pragma: no cover - protocol
        ...

    def subscribe(
        self, event_type: str, handler: EventHandler
    ) -> None:  # pragma: no cover - protocol
        ...


class HttpTransport(Protocol):
    """Minimal protocol for HTTP-style transports used by the execution module."""

    def post(self, path: str, payload: dict[str, Any]) -> Any:  # pragma: no cover - protocol
        ...


@dataclass
class ExecutionTransports:
    """Bundle of transports injected into the execution module."""

    event_bus: EventTransport
    http_client: HttpTransport | None = None


def build_execution_transports(container: Any) -> ExecutionTransports:
    """Build default transports from the shared container."""
    event_bus = container.services.event_bus()
    return ExecutionTransports(event_bus=event_bus, http_client=None)
