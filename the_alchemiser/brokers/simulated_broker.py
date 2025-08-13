"""Simulated broker for backtests."""

from __future__ import annotations

from ..accounting.ledger import Ledger
from ..backtest.events import MarketEvent
from ..execution.engine import ExecutionEngine
from ..execution.models import Account, Fill, Order, Position
from .base import Broker


class SimulatedBroker(Broker):
    """Broker that fills orders against a market data stream."""

    def __init__(self, engine: ExecutionEngine, ledger: Ledger) -> None:
        self.engine = engine
        self.ledger = ledger
        self.orders: dict[str, Order] = {}
        self.fills: list[Fill] = []

    def submit_order(self, order: Order) -> Order:
        self.orders[order.id] = order
        self.engine.submit(order)
        return order

    def get_order(self, order_id: str) -> Order:
        return self.orders[order_id]

    def list_orders(self, status: str = "all") -> list[Order]:
        return list(self.orders.values())

    def get_position(self, symbol: str) -> Position:
        return self.ledger.positions.get(symbol, Position(symbol=symbol))

    def list_positions(self) -> list[Position]:
        return list(self.ledger.positions.values())

    def get_account(self) -> Account:
        return Account(cash=self.ledger.cash)

    def on_market_event(self, event: MarketEvent) -> list[Fill]:
        fills = self.engine.process_event(event)
        for f in fills:
            self.ledger.apply_fill(
                Fill(
                    order_id=f.order_id,
                    symbol=f.symbol,
                    qty=f.qty if self.get_order(f.order_id).side == "buy" else -f.qty,
                    price=f.price,
                    timestamp=f.timestamp,
                )
            )
            self.fills.append(f)
            if f.order_id in self.orders and f.order_id not in self.engine.state.orders:
                self.orders.pop(f.order_id)
        return fills
