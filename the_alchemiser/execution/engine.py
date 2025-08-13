"""Very small execution engine used by the simulated broker.

The goal is to provide deterministic behaviour for unit tests. A proper
implementation would model latency, queue positioning and slippage.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..backtest.events import MarketEvent
from .models import Fill, Order


@dataclass(slots=True)
class EngineState:
    """Tracks open orders."""

    orders: dict[str, Order]


class ExecutionEngine:
    """Processes market data events and generates fills."""

    def __init__(self) -> None:
        self.state = EngineState(orders={})

    def submit(self, order: Order) -> None:
        self.state.orders[order.id] = order

    def cancel(self, order_id: str) -> None:
        self.state.orders.pop(order_id, None)

    def process_event(self, event: MarketEvent) -> list[Fill]:
        fills: list[Fill] = []
        for order in list(self.state.orders.values()):
            if order.symbol != event.symbol:
                continue
            if order.type == "market":
                fill_qty = order.qty - order.filled_qty
                fills.append(
                    Fill(
                        order_id=order.id,
                        symbol=order.symbol,
                        qty=fill_qty,
                        price=event.price,
                        timestamp=event.timestamp,
                    )
                )
                self.state.orders.pop(order.id)
            elif order.type == "limit":
                target = order.limit_price or 0.0
                if order.side == "buy" and event.price <= target:
                    fill_qty = min(order.qty - order.filled_qty, event.size)
                elif order.side == "sell" and event.price >= target:
                    fill_qty = min(order.qty - order.filled_qty, event.size)
                else:
                    continue
                order.filled_qty += fill_qty
                fills.append(
                    Fill(
                        order_id=order.id,
                        symbol=order.symbol,
                        qty=fill_qty,
                        price=event.price,
                        timestamp=event.timestamp,
                    )
                )
                if order.filled_qty >= order.qty:
                    self.state.orders.pop(order.id)
        return fills
