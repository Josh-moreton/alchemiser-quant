"""Temporary adapter exposing get_data-like API on top of MarketDataClient.

This lets us migrate strategies incrementally while removing the legacy facade from DI.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from the_alchemiser.services.market_data.market_data_client import MarketDataClient


# TODO: Phase 3 - Strategy Migration
# Remove this adapter once all strategies consume the typed MarketDataPort directly.
# This is a temporary shim to preserve the legacy get_data/get_latest_quote/current_price
# shapes while using the modern typed MarketDataClient underneath.
# Enforcement: search for usages of TypedDataProviderAdapter and delete them, then remove this file.
class TypedDataProviderAdapter:
    """Adapter to expose legacy get_data/get_latest_quote/current_price shape.

    Not a runtime fallback; only a shim to keep strategy code stable while we migrate
    them to typed MarketDataPort. Remove after Phase 3.
    """

    def __init__(self, api_key: str, secret_key: str) -> None:
        self._client = MarketDataClient(api_key, secret_key)

    def get_data(
        self,
        symbol: str,
        timeframe: str = "1day",
        period: str = "1y",
        **_: Any,
    ) -> pd.DataFrame:
        # Map legacy arg names to MarketDataClient
        interval = "1d" if timeframe.lower() in {"1day", "1d", "day"} else "1m"
        return self._client.get_historical_bars(symbol, period=period, interval=interval)

    def get_latest_quote(self, symbol: str, **_: Any) -> tuple[float | None, float | None]:
        bid, ask = self._client.get_latest_quote(symbol)
        return (bid or None, ask or None)

    def get_current_price(self, symbol: str, **_: Any) -> float | None:
        return self._client.get_current_price_from_quote(symbol)
