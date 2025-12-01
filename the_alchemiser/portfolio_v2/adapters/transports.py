"""Transport adapters for the portfolio module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class EventTransport(Protocol):
    """Protocol for event-style transports used by the portfolio module."""

    def publish(self, event: Any) -> None:  # pragma: no cover - protocol
        ...

    def subscribe(self, event_type: str, handler: Any) -> None:  # pragma: no cover - protocol
        ...


class HttpTransport(Protocol):
    """Minimal protocol for HTTP-style transports used by the portfolio module."""

    def post(self, path: str, payload: dict[str, Any]) -> Any:  # pragma: no cover - protocol
        ...


@dataclass
class PortfolioTransports:
    """Bundle of transports injected into the portfolio module."""

    event_bus: EventTransport
    http_client: HttpTransport | None = None


def build_portfolio_transports(container: Any) -> PortfolioTransports:
    """Build default transports from the shared container."""

    event_bus = container.services.event_bus()
    return PortfolioTransports(event_bus=event_bus, http_client=None)

