"""Strategy market data adapter for DataFrame compatibility.

This adapter bridges strategies that expect DataFrame-based MarketDataPort
to use the canonical domain-based MarketDataPort with Symbol and domain models.

This is a temporary bridge until all strategies are migrated to domain-centric
access patterns.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from the_alchemiser.domain.market_data.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.shared_kernel.value_objects.symbol import Symbol


class StrategyMarketDataAdapter:
    """Adapter implementing DataFrame-based interface over canonical MarketDataPort.

    This adapter allows strategies expecting DataFrame methods to work with the
    canonical domain MarketDataPort without modifying the canonical port interface.
    """

    def __init__(self, canonical_port: MarketDataPort) -> None:
        self._canonical_port = canonical_port

    def get_data(
        self,
        symbol: str,
        timeframe: str = "1day",
        period: str = "1y",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Convert canonical port bars to DataFrame for legacy strategy compatibility."""
        symbol_obj = Symbol(symbol)
        bars = self._canonical_port.get_bars(symbol_obj, period, timeframe)

        # Convert BarModel list to DataFrame
        if not bars:
            return pd.DataFrame()

        data = []
        for bar in bars:
            data.append({
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': float(bar.volume),
                'timestamp': bar.ts
            })

        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index('timestamp', inplace=True)

        return df

    def get_current_price(self, symbol: str, **kwargs: Any) -> float | None:
        """Get current price using canonical port's mid_price method."""
        symbol_obj = Symbol(symbol)
        return self._canonical_port.get_mid_price(symbol_obj)

    def get_latest_quote(self, symbol: str, **kwargs: Any) -> tuple[float | None, float | None]:
        """Get latest quote using canonical port and extract bid/ask."""
        symbol_obj = Symbol(symbol)
        quote = self._canonical_port.get_latest_quote(symbol_obj)

        if quote is None:
            return (None, None)

        # QuoteModel has bid and ask attributes
        bid = float(quote.bid) if quote.bid is not None else None
        ask = float(quote.ask) if quote.ask is not None else None
        return (bid, ask)
