#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Comprehensive test script for all strategies with per-indicator live bar injection.

Tests strategies in two modes:
1. "Historical" mode - Uses market data up to Jan 5th (simulates T-1 behavior)
2. "Live" mode - Uses S3 Jan 6th data with per-indicator live bar injection

This helps validate that the per-indicator approach matches Composer.trade signals.

Usage:
    poetry run python scripts/test_all_strategies.py
    poetry run python scripts/test_all_strategies.py --historical-only
    poetry run python scripts/test_all_strategies.py --live-only
    poetry run python scripts/test_all_strategies.py --strategy simons_kmlm

"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date, timezone
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

# Set environment variables for S3 market data access
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Add functions/strategy_worker to path for imports
strategy_worker_path = Path(__file__).parent.parent / "functions" / "strategy_worker"
sys.path.insert(0, str(strategy_worker_path))

# Add layers/shared to path for shared imports
shared_layer_path = Path(__file__).parent.parent / "layers" / "shared"
sys.path.insert(0, str(shared_layer_path))

if TYPE_CHECKING:
    import pandas as pd
    from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
    from the_alchemiser.shared.value_objects.symbol import Symbol

# The 10 strategies we're validating against Composer (matching strategy.dev.json)
VALIDATION_STRATEGIES = [
    "beam_chain",
    "beefier_3x",
    "bento_collection",
    "ftl_starburst",
    "gold",
    "nuclear_feaver",
    "rains_em_dancer",
    "simons_kmlm",
    "sisyphus_lowvol",
    "tqqq_ftlt",
]

# Test dates
HISTORICAL_DATE = date(2026, 1, 5)  # T-1 reference
LIVE_DATE = date(2026, 1, 6)  # "Today" for live test


@dataclass
class StrategyResult:
    """Result from running a strategy."""

    strategy_name: str
    mode: str  # "historical" or "live"
    allocation: dict[str, float]
    error: str | None = None

    def symbols_str(self) -> str:
        """Get comma-separated list of symbols with weights."""
        if self.error:
            return f"ERROR: {self.error}"
        if not self.allocation:
            return "NO ALLOCATION"
        return ", ".join(f"{sym}: {weight:.2%}" for sym, weight in sorted(self.allocation.items()))


def create_historical_adapter(cutoff_date: date) -> "HistoricalMarketDataAdapter":
    """Create adapter that returns data up to cutoff date only."""
    import pandas as pd

    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.types.market_data import BarModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol

    class HistoricalMarketDataAdapter(MarketDataPort):
        """Adapter that returns market data up to a cutoff date."""

        def __init__(self, cutoff: date):
            self.cutoff_date = cutoff
            self.market_data_store = MarketDataStore()
            self._cache: dict[str, pd.DataFrame] = {}

        def _get_dataframe(self, symbol: str) -> pd.DataFrame:
            """Get DataFrame for symbol, cached."""
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

        def get_bars(
            self,
            symbol: Symbol,
            period: str,
            timeframe: str,
        ) -> list[BarModel]:
            """Get bars filtered to cutoff date."""
            import pandas as pd

            symbol_str = str(symbol)
            df = self._get_dataframe(symbol_str)

            if df.empty:
                return []

            cutoff_datetime = pd.Timestamp(self.cutoff_date, tz=timezone.utc)

            if df.index.tz is None:
                df.index = df.index.tz_localize(timezone.utc)

            df_filtered = df[df.index.normalize() <= cutoff_datetime]

            if df_filtered.empty:
                return []

            bars: list[BarModel] = []
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

        def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
            """Get latest bar as of cutoff date."""
            bars = self.get_bars(symbol, "1D", "1D")
            return bars[-1] if bars else None

        def get_quote(self, symbol: Symbol) -> "QuoteModel | None":
            """Get quote - not used in historical mode."""
            return None

    return HistoricalMarketDataAdapter(cutoff_date)


def create_per_indicator_adapter(
    live_date: date, historical_date: date
) -> "PerIndicatorMarketDataAdapter":
    """Create adapter with per-indicator T-1 logic.

    RSI, current_price, moving_average: use live_date
    stdev_return, cumulative_return: use historical_date (T-1)
    """
    import pandas as pd

    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.types.market_data import BarModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol

    HISTORICAL_ONLY_INDICATORS = {
        "stdev_return",
        "stdev_price",
        "cumulative_return",
        "max_drawdown",
    }

    class PerIndicatorMarketDataAdapter(MarketDataPort):
        """Adapter with per-indicator date handling."""

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
            bars: list[BarModel] = []
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
            # Default to live date
            return self._get_bars_for_date(symbol, self.live_date)

        def get_bars_for_indicator(
            self, symbol: Symbol, period: str, timeframe: str, indicator_type: str
        ) -> list[BarModel]:
            """Per-indicator date logic."""
            if indicator_type in HISTORICAL_ONLY_INDICATORS:
                return self._get_bars_for_date(symbol, self.historical_date)
            return self._get_bars_for_date(symbol, self.live_date)

        def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
            bars = self.get_bars(symbol, "1D", "1D")
            return bars[-1] if bars else None

        def get_quote(self, symbol: Symbol) -> "QuoteModel | None":
            return None

    return PerIndicatorMarketDataAdapter(live_date, historical_date)


def run_strategy_historical(strategy_name: str) -> StrategyResult:
    """Run strategy with historical data only (up to Jan 5th)."""
    try:
        from engines.dsl.engine import DslEngine

        strategies_path = shared_layer_path / "the_alchemiser" / "shared" / "strategies"
        strategy_file = f"{strategy_name}.clj"
        full_path = strategies_path / strategy_file

        if not full_path.exists():
            return StrategyResult(
                strategy_name=strategy_name,
                mode="historical",
                allocation={},
                error=f"Strategy file not found: {strategy_file}",
            )

        # Create historical adapter with Jan 5th cutoff
        market_data_adapter = create_historical_adapter(HISTORICAL_DATE)

        engine = DslEngine(
            strategy_config_path=strategies_path,
            market_data_adapter=market_data_adapter,
            debug_mode=False,
        )

        correlation_id = f"test-historical-{strategy_name}"
        allocation, _ = engine.evaluate_strategy(strategy_file, correlation_id)

        return StrategyResult(
            strategy_name=strategy_name,
            mode="historical",
            allocation={k: float(v) for k, v in allocation.target_weights.items()},
        )

    except Exception as e:
        return StrategyResult(
            strategy_name=strategy_name,
            mode="historical",
            allocation={},
            error=str(e),
        )


def run_strategy_live(strategy_name: str) -> StrategyResult:
    """Run strategy with Jan 6th data (simulates live with per-indicator T-1)."""
    try:
        from engines.dsl.engine import DslEngine

        strategies_path = shared_layer_path / "the_alchemiser" / "shared" / "strategies"
        strategy_file = f"{strategy_name}.clj"
        full_path = strategies_path / strategy_file

        if not full_path.exists():
            return StrategyResult(
                strategy_name=strategy_name,
                mode="live",
                allocation={},
                error=f"Strategy file not found: {strategy_file}",
            )

        # Create per-indicator adapter: RSI uses Jan 6, stdev uses Jan 5 (T-1)
        market_data_adapter = create_per_indicator_adapter(LIVE_DATE, HISTORICAL_DATE)

        engine = DslEngine(
            strategy_config_path=strategies_path,
            market_data_adapter=market_data_adapter,
            debug_mode=False,
        )

        correlation_id = f"test-live-{strategy_name}"
        allocation, _ = engine.evaluate_strategy(strategy_file, correlation_id)

        return StrategyResult(
            strategy_name=strategy_name,
            mode="live",
            allocation={k: float(v) for k, v in allocation.target_weights.items()},
        )

    except Exception as e:
        return StrategyResult(
            strategy_name=strategy_name,
            mode="live",
            allocation={},
            error=str(e),
        )


def print_results_table(results: list[StrategyResult]) -> None:
    """Print results in a formatted table."""
    # Group by strategy
    by_strategy: dict[str, dict[str, StrategyResult]] = {}
    for result in results:
        if result.strategy_name not in by_strategy:
            by_strategy[result.strategy_name] = {}
        by_strategy[result.strategy_name][result.mode] = result

    # Calculate column widths
    max_name_len = max(len(s) for s in VALIDATION_STRATEGIES)
    col_width = max(40, max_name_len)

    # Print header
    print("\n" + "=" * 120)
    print("STRATEGY TEST RESULTS")
    print(f"Historical: {HISTORICAL_DATE} (all indicators use this date)")
    print(f"Live: {LIVE_DATE} (RSI uses Jan 6, stdev uses Jan 5 via T-1)")
    print("=" * 120)

    print(
        f"\n{'Strategy':<{max_name_len}} | {'Historical (Jan 5)':<{col_width}} | {'Live (Jan 6 + T-1 for stdev)':<{col_width}}"
    )
    print("-" * (max_name_len + col_width * 2 + 6))

    for strategy in VALIDATION_STRATEGIES:
        if strategy not in by_strategy:
            continue

        hist_result = by_strategy[strategy].get("historical")
        live_result = by_strategy[strategy].get("live")

        hist_str = hist_result.symbols_str() if hist_result else "NOT RUN"
        live_str = live_result.symbols_str() if live_result else "NOT RUN"

        # Truncate if too long
        if len(hist_str) > col_width:
            hist_str = hist_str[: col_width - 3] + "..."
        if len(live_str) > col_width:
            live_str = live_str[: col_width - 3] + "..."

        print(f"{strategy:<{max_name_len}} | {hist_str:<{col_width}} | {live_str:<{col_width}}")

    print("-" * (max_name_len + col_width * 2 + 6))


def print_detailed_results(results: list[StrategyResult]) -> None:
    """Print detailed results for each strategy."""
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    current_strategy = None
    for result in sorted(results, key=lambda r: (r.strategy_name, r.mode)):
        if result.strategy_name != current_strategy:
            current_strategy = result.strategy_name
            print(f"\n{'-' * 60}")
            print(f"  {current_strategy.upper()}")
            print(f"{'-' * 60}")

        print(f"\n  [{result.mode.upper()}]")
        if result.error:
            print(f"    ERROR: {result.error}")
        elif not result.allocation:
            print("    NO ALLOCATION")
        else:
            total = sum(result.allocation.values())
            for sym, weight in sorted(result.allocation.items()):
                print(f"    {sym}: {weight:.4f} ({weight:.2%})")
            print(f"    TOTAL: {total:.4f}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test all strategies with historical and live modes"
    )
    parser.add_argument(
        "--historical-only",
        action="store_true",
        help="Only run historical tests (Jan 5th cutoff)",
    )
    parser.add_argument(
        "--live-only",
        action="store_true",
        help="Only run live tests (per-indicator live bar injection)",
    )
    parser.add_argument(
        "--strategy",
        "-s",
        help="Test only a specific strategy",
    )
    parser.add_argument(
        "--detailed",
        "-d",
        action="store_true",
        help="Show detailed results with full allocations",
    )

    args = parser.parse_args()

    # Determine which strategies to test
    strategies = VALIDATION_STRATEGIES
    if args.strategy:
        if args.strategy not in VALIDATION_STRATEGIES:
            print(f"Warning: {args.strategy} not in validation list, but will run anyway")
        strategies = [args.strategy]

    # Determine which modes to run
    run_historical = not args.live_only
    run_live = not args.historical_only

    results: list[StrategyResult] = []

    print(f"\nTesting {len(strategies)} strategies...")
    print(f"Modes: {'Historical' if run_historical else ''} {'Live' if run_live else ''}")
    print()

    for i, strategy in enumerate(strategies, 1):
        print(f"[{i}/{len(strategies)}] {strategy}...", end=" ", flush=True)

        if run_historical:
            hist_result = run_strategy_historical(strategy)
            results.append(hist_result)
            status = "✓" if not hist_result.error else "✗"
            print(f"hist:{status}", end=" ", flush=True)

        if run_live:
            live_result = run_strategy_live(strategy)
            results.append(live_result)
            status = "✓" if not live_result.error else "✗"
            print(f"live:{status}", end=" ", flush=True)

        print()

    # Print results
    print_results_table(results)

    if args.detailed:
        print_detailed_results(results)

    # Summary
    errors = [r for r in results if r.error]
    if errors:
        print(f"\n⚠️  {len(errors)} errors encountered:")
        for e in errors:
            print(f"   - {e.strategy_name} ({e.mode}): {e.error}")

    print(f"\n✅ {len(results) - len(errors)}/{len(results)} tests completed successfully")


if __name__ == "__main__":
    main()
