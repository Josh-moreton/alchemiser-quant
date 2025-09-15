"""Business Unit: shared | Status: current.

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
    """Domain port for accessing market data providers.

    Provides a minimal interface used by strategy engines to fetch
    historical bars and current quotes via a shared abstraction.
    """

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Historical bars for a symbol.

        period/timeframe kept as strings initially to avoid broad refactors.
        """
        ...

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get the latest bid/ask quote for a symbol if available."""
        ...

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get current mid price derived from the latest quote, if available."""
        ...
