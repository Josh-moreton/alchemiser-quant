"""Test fakes for port protocols."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from the_alchemiser.domain.types import AccountInfo, OrderDetails, PositionsDict
from the_alchemiser.ports import (
    Clock,
    MarketData,
    Notifier,
    OrderExecution,
    PositionStore,
    RiskChecks,
)


class FakeMarketData(MarketData):
    def __init__(self, prices: dict[str, float] | None = None) -> None:
        self._prices = prices or {}

    def get_current_price(self, symbol: str) -> float:  # pragma: no cover - simple
        return self._prices.get(symbol, 0.0)

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        return {s: self.get_current_price(s) for s in symbols}


class FakeOrderExecution(OrderExecution):
    def __init__(self) -> None:
        self.orders: list[OrderDetails] = []

    def place_order(self, order: OrderDetails) -> str | None:
        self.orders.append(order)
        return order.get("id")

    def wait_for_settlement(
        self, order_ids: list[str], max_wait_time: int, poll_interval: float
    ) -> bool:  # noqa: ARG002
        return True


class FakeRiskChecks(RiskChecks):
    def validate_order(self, order: OrderDetails) -> bool:  # pragma: no cover - trivial
        return True

    def check_positions(self, positions: PositionsDict) -> bool:  # pragma: no cover - trivial
        return True


class FakePositionStore(PositionStore):
    def __init__(self, account: AccountInfo, positions: PositionsDict) -> None:
        self._account = account
        self._positions = positions

    def get_account_info(self) -> AccountInfo:
        return self._account

    def get_positions(self) -> PositionsDict:
        return self._positions


class FakeClock(Clock):
    def now(self) -> datetime:
        return datetime(2000, 1, 1)

    def sleep(self, seconds: float) -> None:  # pragma: no cover - trivial
        pass


class FakeNotifier(Notifier):
    def send(
        self, message: str, *, subject: str | None = None, **kwargs: Any
    ) -> None:  # pragma: no cover - trivial
        self.last_message = message
        self.last_subject = subject
        self.last_kwargs = kwargs
