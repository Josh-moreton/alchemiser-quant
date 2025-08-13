"""Lot-level FIFO ledger for the backtest engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..execution.models import Fill, Position, PositionLot


@dataclass(slots=True)
class Ledger:
    """Tracks positions and realised P&L."""

    positions: dict[str, Position] = field(default_factory=dict)
    realised_pnl: float = 0.0
    cash: float = 0.0

    def apply_fill(self, fill: Fill) -> None:
        pos = self.positions.setdefault(fill.symbol, Position(symbol=fill.symbol))
        if fill.qty > 0:  # buy
            pos.lots.append(PositionLot(qty=fill.qty, price=fill.price))
            self.cash -= fill.qty * fill.price
        else:  # sell
            qty_to_close = -fill.qty
            while qty_to_close > 0 and pos.lots:
                lot = pos.lots[0]
                take = min(lot.qty, qty_to_close)
                self.realised_pnl += take * (fill.price - lot.price)
                lot.qty -= take
                qty_to_close -= take
                if lot.qty == 0:
                    pos.lots.pop(0)
            self.cash += -fill.qty * fill.price
