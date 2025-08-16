"""Core port definitions for application layer.

These protocol interfaces describe the behaviour required by the trading
application.  Concrete implementations live in the ``adapters`` package.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from the_alchemiser.domain.types import AccountInfo, OrderDetails, PositionsDict


class MarketData(Protocol):
    """Retrieve market pricing information."""

    def get_current_price(self, symbol: str) -> float: ...

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]: ...


class OrderExecution(Protocol):
    """Execute orders against a brokerage."""

    def place_order(self, order: OrderDetails) -> str | None: ...

    def wait_for_settlement(
        self, order_ids: list[str], max_wait_time: int, poll_interval: float
    ) -> bool: ...


class RiskChecks(Protocol):
    """Run pre-trade risk validations."""

    def validate_order(self, order: OrderDetails) -> bool: ...

    def check_positions(self, positions: PositionsDict) -> bool: ...


class PositionStore(Protocol):
    """Access account and position information."""

    def get_account_info(self) -> AccountInfo: ...

    def get_positions(self) -> PositionsDict: ...


class Clock(Protocol):
    """Abstract clock for scheduling and timing."""

    def now(self) -> datetime: ...

    def sleep(self, seconds: float) -> None: ...


class Notifier(Protocol):
    """Send user or system notifications."""

    def send(self, message: str, *, subject: str | None = None, **kwargs: Any) -> None: ...
