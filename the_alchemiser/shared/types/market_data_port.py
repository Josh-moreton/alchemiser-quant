"""Business Unit: utilities; Status: current.

Domain port for market data access.

This port defines the minimal contract strategies need.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from the_alchemiser.shared.types.market_data import BarModel
from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.value_objects.symbol import Symbol


@runtime_checkable
class MarketDataPort(Protocol):
    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Historical bars for a symbol.

        period/timeframe kept as strings initially to avoid broad refactors.
        """
        ...

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None: ...

    def get_mid_price(self, symbol: Symbol) -> float | None: ...
