"""Utility helpers for writing backtest artefacts to disk."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from ..execution.models import Fill, Order


class ArtefactWriter:
    """Writes orders, fills and summary statistics."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def write_orders(self, orders: Iterable[Order]) -> None:
        path = self.root / "orders.csv"
        with path.open("w") as fh:
            fh.write("id,symbol,qty,side,type,limit_price\n")
            for o in orders:
                fh.write(f"{o.id},{o.symbol},{o.qty},{o.side},{o.type},{o.limit_price or ''}\n")

    def write_fills(self, fills: Iterable[Fill]) -> None:
        path = self.root / "fills.csv"
        with path.open("w") as fh:
            fh.write("order_id,symbol,qty,price,timestamp\n")
            for f in fills:
                fh.write(f"{f.order_id},{f.symbol},{f.qty},{f.price},{f.timestamp.isoformat()}\n")

    def write_stats(self, stats: dict[str, float]) -> None:
        path = self.root / "stats.json"
        with path.open("w") as fh:
            json.dump(stats, fh)
