"""Broker interface mirroring a subset of Alpaca's SDK."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..execution.models import Account, Order, Position


class Broker(ABC):
    """Abstract broker interface."""

    @abstractmethod
    def submit_order(self, order: Order) -> Order:  # pragma: no cover - interface
        ...

    @abstractmethod
    def get_order(self, order_id: str) -> Order:  # pragma: no cover - interface
        ...

    @abstractmethod
    def list_orders(self, status: str = "all") -> list[Order]:  # pragma: no cover
        ...

    @abstractmethod
    def get_position(self, symbol: str) -> Position:  # pragma: no cover
        ...

    @abstractmethod
    def list_positions(self) -> list[Position]:  # pragma: no cover
        ...

    @abstractmethod
    def get_account(self) -> Account:  # pragma: no cover
        ...
