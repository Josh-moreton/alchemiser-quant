"""Market data replayer merging multi-symbol streams into a single iterator."""

from __future__ import annotations

import random
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..backtest.events import MarketEvent


@dataclass(slots=True)
class MarketDataReplayer:
    """Yield market events in time order."""

    events: list[MarketEvent]

    def __iter__(self) -> Iterator[MarketEvent]:
        yield from sorted(self.events, key=lambda e: (e.timestamp, e.symbol))

    @classmethod
    def synthetic(
        cls,
        start: datetime,
        end: datetime,
        symbols: list[str],
        seed: int,
        interval_minutes: int = 1,
    ) -> MarketDataReplayer:
        rng = random.Random(seed)
        events: list[MarketEvent] = []
        ts = start
        prices = dict.fromkeys(symbols, 100.0)
        while ts <= end:
            for sym in symbols:
                prices[sym] += rng.random() - 0.5
                events.append(MarketEvent(timestamp=ts, symbol=sym, price=prices[sym]))
            ts += timedelta(minutes=interval_minutes)
        return cls(events=events)
