#!/usr/bin/env python3
"""Debug script to verify per-indicator routing."""

import os
from datetime import date, timezone
from decimal import Decimal
from pathlib import Path
import sys

os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

shared_layer_path = Path(__file__).parent.parent / "layers" / "shared"
strategy_worker_path = Path(__file__).parent.parent / "functions" / "strategy_worker"
sys.path.insert(0, str(strategy_worker_path))
sys.path.insert(0, str(shared_layer_path))

import pandas as pd

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.types.market_data import BarModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol

HISTORICAL_DATE = date(2026, 1, 5)
LIVE_DATE = date(2026, 1, 6)

HISTORICAL_ONLY_INDICATORS = {"stdev_return", "stdev_price", "cumulative_return", "max_drawdown"}


class DebugPerIndicatorAdapter(MarketDataPort):
    """Adapter with debug output for per-indicator routing."""

    def __init__(self, live: date, historical: date):
        self.live_date = live
        self.historical_date = historical
        self.market_data_store = MarketDataStore()
        self._cache: dict[str, pd.DataFrame] = {}

    def _get_dataframe(self, symbol: str) -> pd.DataFrame:
        if symbol not in self._cache:
            df = self.market_data_store.read_symbol_data(symbol)
            if df is not None and not df.empty:
                if "timestamp" in df.columns:
                    df = df.set_index("timestamp")
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                self._cache[symbol] = df
            else:
                return pd.DataFrame()
        return self._cache[symbol]

    def _get_bars_for_date(self, symbol: Symbol, cutoff: date) -> list[BarModel]:
        symbol_str = str(symbol)
        df = self._get_dataframe(symbol_str)
        if df.empty:
            return []
        cutoff_datetime = pd.Timestamp(cutoff, tz=timezone.utc)
        if df.index.tz is None:
            df.index = df.index.tz_localize(timezone.utc)
        df_filtered = df[df.index.normalize() <= cutoff_datetime]
        if df_filtered.empty:
            return []
        bars = []
        for ts, row in df_filtered.iterrows():
            bar = BarModel(
                symbol=symbol_str,
                timestamp=ts.to_pydatetime(),
                open=Decimal(str(row.get("open", row.get("Open", 0)))),
                high=Decimal(str(row.get("high", row.get("High", 0)))),
                low=Decimal(str(row.get("low", row.get("Low", 0)))),
                close=Decimal(str(row.get("close", row.get("Close", 0)))),
                volume=int(row.get("volume", row.get("Volume", 0))),
            )
            bars.append(bar)
        return bars

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        return self._get_bars_for_date(symbol, self.live_date)

    def get_bars_for_indicator(
        self, symbol: Symbol, period: str, timeframe: str, indicator_type: str
    ) -> list[BarModel]:
        if indicator_type in HISTORICAL_ONLY_INDICATORS:
            print(f"[T-1] {indicator_type} for {symbol}: using {self.historical_date}")
            return self._get_bars_for_date(symbol, self.historical_date)
        print(f"[LIVE] {indicator_type} for {symbol}: using {self.live_date}")
        return self._get_bars_for_date(symbol, self.live_date)

    def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
        bars = self.get_bars(symbol, "1D", "1D")
        return bars[-1] if bars else None

    def get_quote(self, symbol: Symbol):
        return None


def main():
    from engines.dsl.engine import DslEngine

    adapter = DebugPerIndicatorAdapter(LIVE_DATE, HISTORICAL_DATE)
    strategies_path = shared_layer_path / "the_alchemiser" / "shared" / "strategies"
    
    engine = DslEngine(
        strategy_config_path=strategies_path,
        market_data_adapter=adapter,
        debug_mode=False,
    )

    print("\n=== Running bento_collection ===")
    allocation, _ = engine.evaluate_strategy("bento_collection.clj", "test-bento")
    print(f"\nRESULT: {dict(allocation.target_weights)}")


if __name__ == "__main__":
    main()
