"""Business Unit: execution | Status: current

Order Lifecycle Adapter - migrated from legacy location.
"""


from __future__ import annotations

from typing import Any, Protocol

from the_alchemiser.domain.trading.protocols.order_lifecycle import (
    OrderLifecycleMonitor,
)
from the_alchemiser.execution.monitoring.websocket_order_monitor import (
    OrderCompletionMonitor,
)
from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO


class TradingClientProtocol(Protocol):  # pragma: no cover - structural typing
    """Minimal protocol for the Alpaca trading client used by the websocket monitor."""

    def get_order_by_id(self, order_id: str) -> Any:  # noqa: ANN401 - runtime library object
        """Retrieve order by ID (runtime return type from alpaca-py)."""
        ...


class WebSocketOrderLifecycleAdapter(OrderLifecycleMonitor):  # pragma: no cover - thin adapter
    """Concrete adapter implementing the lifecycle Protocol via websocket-based monitor."""

    def __init__(
        self,
        trading_client: TradingClientProtocol,
        api_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        """Create adapter with provided trading client and optional explicit credentials."""
        self._monitor = OrderCompletionMonitor(
            trading_client, api_key=api_key, secret_key=secret_key
        )

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 60
    ) -> WebSocketResultDTO:
        """Delegate to underlying websocket monitor to await terminal order states."""
        return self._monitor.wait_for_order_completion(order_ids, max_wait_seconds=max_wait_seconds)
