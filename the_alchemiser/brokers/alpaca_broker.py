"""Thin wrapper around Alpaca's SDK.

Currently a placeholder to keep surface compatibility. Live trading uses the
existing implementation under ``the_alchemiser.services``; this module exists
so the backtest runner can switch between a simulated and real broker without
altering external code.
"""

from __future__ import annotations

from ..execution.models import Account, Order, Position
from .base import Broker


class AlpacaBroker(Broker):
    """Placeholder broker delegating to the Alpaca SDK."""

    def submit_order(self, order: Order) -> Order:  # pragma: no cover - TODO
        raise NotImplementedError("Integrate alpaca-py SDK")

    def get_order(self, order_id: str) -> Order:  # pragma: no cover - TODO
        raise NotImplementedError

    def list_orders(self, status: str = "all") -> list[Order]:  # pragma: no cover - TODO
        raise NotImplementedError

    def get_position(self, symbol: str) -> Position:  # pragma: no cover - TODO
        raise NotImplementedError

    def list_positions(self) -> list[Position]:  # pragma: no cover - TODO
        raise NotImplementedError

    def get_account(self) -> Account:  # pragma: no cover - TODO
        raise NotImplementedError
