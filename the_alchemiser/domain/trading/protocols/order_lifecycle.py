from __future__ import annotations

from typing import Protocol

from the_alchemiser.interfaces.schemas.execution import WebSocketResultDTO

"""Protocol for order lifecycle monitoring.

Allows application layer executors to wait for order completion without
depending directly on infrastructure websocket implementation.
"""


class OrderLifecycleMonitor(Protocol):  # pragma: no cover - structural typing
    """Protocol abstraction for order lifecycle monitoring."""

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 60
    ) -> WebSocketResultDTO:
        """Wait for the provided order IDs to reach a terminal state."""
        ...
