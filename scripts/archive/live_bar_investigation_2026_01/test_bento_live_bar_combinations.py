#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Test Bento Collection with all 256 combinations of use_live_bar settings.

For each indicator, use_live_bar=True means include Jan 6th data,
use_live_bar=False means use Jan 5th data only (T-1).

Known correct signal: BIL 88.5%, LABU 2.5%, SARK 9.0%

Usage:
    poetry run python scripts/test_bento_live_bar_combinations.py
    poetry run python scripts/test_bento_live_bar_combinations.py --workers 16

"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from itertools import product
from pathlib import Path
from typing import Any

# Set environment variables for S3 market data access
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Add paths for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
STRATEGY_WORKER_PATH = PROJECT_ROOT / "functions" / "strategy_worker"
SHARED_LAYER_PATH = PROJECT_ROOT / "layers" / "shared"

sys.path.insert(0, str(STRATEGY_WORKER_PATH))
sys.path.insert(0, str(SHARED_LAYER_PATH))

# Test dates
LIVE_DATE = date(2026, 1, 6)  # "Today" - use_live_bar=True uses this
HISTORICAL_DATE = date(2026, 1, 5)  # T-1 - use_live_bar=False uses this

# All 8 indicators used by Bento Collection
BENTO_INDICATORS = [
    "current_price",
    "rsi",
    "moving_average",
    "moving_average_return",
    "cumulative_return",
    "exponential_moving_average_price",
    "max_drawdown",
    "stdev_return",
]

# Known correct allocation from Composer
CORRECT_ALLOCATION = {
    "BIL": 0.885,
    "LABU": 0.025,
    "SARK": 0.09,
}


@dataclass
class CombinationResult:
    """Result from running a single combination."""

    combination_id: int
    indicator_settings: dict[str, bool]
    allocation: dict[str, float]
    matches_correct: bool
    error: str | None = None

    def to_csv_row(self) -> dict[str, Any]:
        """Convert to CSV row dict."""
        row: dict[str, Any] = {
            "combination_id": self.combination_id,
            "matches_correct": self.matches_correct,
        }
        # Add indicator settings
        for indicator in BENTO_INDICATORS:
            row[f"{indicator}_live"] = self.indicator_settings.get(indicator, False)

        # Add allocation
        row["allocation"] = (
            "; ".join(f"{k}:{v:.4f}" for k, v in sorted(self.allocation.items()))
            if self.allocation
            else ""
        )
        row["error"] = self.error or ""
        return row


def allocation_matches(alloc: dict[str, float], correct: dict[str, float], tol: float = 0.001) -> bool:
    """Check if allocation matches correct allocation within tolerance."""
    if set(alloc.keys()) != set(correct.keys()):
        return False
    for k, v in correct.items():
        if abs(alloc.get(k, 0) - v) > tol:
            return False
    return True


def run_single_combination(args: tuple[int, dict[str, bool]]) -> CombinationResult:
    """Run Bento Collection with a specific indicator configuration.
    
    This function runs in a subprocess, so we need to reimport everything.
    """
    import os
    import sys
    from datetime import date, timezone
    from decimal import Decimal
    from pathlib import Path

    import pandas as pd

    # Re-set paths for subprocess
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    strategy_worker_path = project_root / "functions" / "strategy_worker"
    shared_layer_path = project_root / "layers" / "shared"

    if str(strategy_worker_path) not in sys.path:
        sys.path.insert(0, str(strategy_worker_path))
    if str(shared_layer_path) not in sys.path:
        sys.path.insert(0, str(shared_layer_path))

    os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

    combination_id, indicator_settings = args
    live_date = date(2026, 1, 6)
    historical_date = date(2026, 1, 5)

    try:
        from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
        from the_alchemiser.shared.types.market_data import BarModel
        from the_alchemiser.shared.types.market_data_port import MarketDataPort
        from the_alchemiser.shared.value_objects.symbol import Symbol

        class ConfigurableMarketDataAdapter(MarketDataPort):
            """Adapter that returns data based on per-indicator settings."""

            def __init__(
                self,
                indicator_settings: dict[str, bool],
                live: date,
                historical: date,
            ):
                self.indicator_settings = indicator_settings
                self.live_date = live
                self.historical_date = historical
                self.market_data_store = MarketDataStore()
                self._cache: dict[str, pd.DataFrame] = {}
                self._current_indicator: str | None = None

            def set_current_indicator(self, indicator_type: str) -> None:
                """Set which indicator is currently being computed."""
                self._current_indicator = indicator_type

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

            def _get_cutoff_date(self) -> date:
                """Get cutoff date based on current indicator."""
                if self._current_indicator is None:
                    # Default to live if no indicator context
                    return self.live_date
                use_live = self.indicator_settings.get(self._current_indicator, True)
                return self.live_date if use_live else self.historical_date

            def get_bars(
                self,
                symbol: Symbol,
                period: str,
                timeframe: str,
            ) -> list[BarModel]:
                symbol_str = str(symbol)
                df = self._get_dataframe(symbol_str)

                if df.empty:
                    return []

                cutoff = self._get_cutoff_date()
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
                        is_incomplete=False,  # S3 data is always complete
                    )
                    bars.append(bar)

                return bars

            def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
                bars = self.get_bars(symbol, "1D", "1D")
                return bars[-1] if bars else None

            def get_quote(self, symbol: Symbol) -> None:
                return None

        # Monkey-patch IndicatorService to set current indicator on adapter
        from indicators.indicator_service import IndicatorService

        original_get_indicator = IndicatorService.get_indicator

        def patched_get_indicator(self, request):
            if hasattr(self.market_data_service, "set_current_indicator"):
                self.market_data_service.set_current_indicator(request.indicator_type)
            return original_get_indicator(self, request)

        IndicatorService.get_indicator = patched_get_indicator

        # Now run the strategy
        from engines.dsl.engine import DslEngine

        strategies_path = shared_layer_path / "the_alchemiser" / "shared" / "strategies"
        strategy_file = "bento_collection.clj"

        market_data_adapter = ConfigurableMarketDataAdapter(
            indicator_settings=indicator_settings,
            live=live_date,
            historical=historical_date,
        )

        engine = DslEngine(
            strategy_config_path=strategies_path,
            market_data_adapter=market_data_adapter,
            debug_mode=False,
        )

        correlation_id = f"bento-combo-{combination_id}"
        allocation_result, _ = engine.evaluate_strategy(strategy_file, correlation_id)

        allocation = {k: float(v) for k, v in allocation_result.target_weights.items()}

        # Check if matches correct
        correct = {
            "BIL": 0.885,
            "LABU": 0.025,
            "SARK": 0.09,
        }
        matches = allocation_matches(allocation, correct)

        return CombinationResult(
            combination_id=combination_id,
            indicator_settings=indicator_settings,
            allocation=allocation,
            matches_correct=matches,
        )

    except Exception as e:
        import traceback

        return CombinationResult(
            combination_id=combination_id,
            indicator_settings=indicator_settings,
            allocation={},
            matches_correct=False,
            error=f"{type(e).__name__}: {e}\n{traceback.format_exc()[:500]}",
        )


def generate_all_combinations() -> list[tuple[int, dict[str, bool]]]:
    """Generate all 256 combinations of indicator settings."""
    combinations = []
    for i, settings in enumerate(product([False, True], repeat=len(BENTO_INDICATORS))):
        indicator_settings = dict(zip(BENTO_INDICATORS, settings))
        combinations.append((i, indicator_settings))
    return combinations


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Bento Collection with all 256 use_live_bar combinations"
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=os.cpu_count() or 8,
        help="Number of parallel workers (default: CPU count)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="bento_live_bar_combinations.csv",
        help="Output CSV file (default: bento_live_bar_combinations.csv)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("BENTO COLLECTION - LIVE BAR COMBINATIONS TEST")
    print("=" * 80)
    print(f"Live date (use_live_bar=True):     {LIVE_DATE}")
    print(f"Historical date (use_live_bar=False): {HISTORICAL_DATE}")
    print(f"Expected correct allocation: {CORRECT_ALLOCATION}")
    print(f"Indicators: {BENTO_INDICATORS}")
    print(f"Total combinations: 2^{len(BENTO_INDICATORS)} = {2**len(BENTO_INDICATORS)}")
    print(f"Workers: {args.workers}")
    print(f"Output: {args.output}")
    print("=" * 80)

    combinations = generate_all_combinations()
    print(f"\nGenerated {len(combinations)} combinations")

    results: list[CombinationResult] = []
    start_time = datetime.now()

    print(f"\nRunning {len(combinations)} combinations with {args.workers} workers...")
    print()

    completed = 0
    matches_found = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(run_single_combination, combo): combo[0]
            for combo in combinations
        }

        for future in as_completed(futures):
            combo_id = futures[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1

                if result.matches_correct:
                    matches_found += 1
                    # Print matching combination immediately
                    settings_str = ", ".join(
                        f"{k}={'T' if v else 'F'}"
                        for k, v in result.indicator_settings.items()
                    )
                    print(f"✓ MATCH #{matches_found} (combo {combo_id}): {settings_str}")

                # Progress update every 16 combinations
                if completed % 16 == 0 or completed == len(combinations):
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = completed / elapsed if elapsed > 0 else 0
                    remaining = (len(combinations) - completed) / rate if rate > 0 else 0
                    print(
                        f"  Progress: {completed}/{len(combinations)} "
                        f"({100*completed/len(combinations):.1f}%) - "
                        f"{rate:.1f}/sec - ETA: {remaining:.0f}s - "
                        f"Matches: {matches_found}"
                    )

            except Exception as e:
                print(f"  ERROR combo {combo_id}: {e}")
                results.append(
                    CombinationResult(
                        combination_id=combo_id,
                        indicator_settings=combinations[combo_id][1],
                        allocation={},
                        matches_correct=False,
                        error=str(e),
                    )
                )
                completed += 1

    elapsed = (datetime.now() - start_time).total_seconds()
    print()
    print("=" * 80)
    print(f"COMPLETED in {elapsed:.1f}s")
    print("=" * 80)

    # Sort results by combination_id
    results.sort(key=lambda r: r.combination_id)

    # Write CSV
    output_path = PROJECT_ROOT / args.output
    fieldnames = (
        ["combination_id", "matches_correct"]
        + [f"{ind}_live" for ind in BENTO_INDICATORS]
        + ["allocation", "error"]
    )

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_csv_row())

    print(f"\nResults written to: {output_path}")

    # Summary
    matching = [r for r in results if r.matches_correct]
    errors = [r for r in results if r.error]

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total combinations tested: {len(results)}")
    print(f"Matching correct allocation: {len(matching)}")
    print(f"Errors: {len(errors)}")

    if matching:
        print(f"\n✓ MATCHING COMBINATIONS ({len(matching)}):")
        for r in matching:
            settings_str = ", ".join(
                f"{k}={'True' if v else 'False'}"
                for k, v in r.indicator_settings.items()
            )
            print(f"  Combo {r.combination_id}: {settings_str}")

    if errors:
        print(f"\n✗ ERRORS ({len(errors)}):")
        for r in errors[:5]:  # Show first 5 errors
            print(f"  Combo {r.combination_id}: {r.error[:100]}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")

    # Find unique allocations
    unique_allocations: dict[str, list[int]] = {}
    for r in results:
        if not r.error:
            alloc_key = "; ".join(f"{k}:{v:.4f}" for k, v in sorted(r.allocation.items()))
            if alloc_key not in unique_allocations:
                unique_allocations[alloc_key] = []
            unique_allocations[alloc_key].append(r.combination_id)

    print(f"\nUnique allocations found: {len(unique_allocations)}")
    for alloc, combo_ids in sorted(unique_allocations.items(), key=lambda x: -len(x[1])):
        is_correct = alloc == "; ".join(f"{k}:{v:.4f}" for k, v in sorted(CORRECT_ALLOCATION.items()))
        marker = "✓" if is_correct else " "
        print(f"  {marker} {alloc} ({len(combo_ids)} combos)")


if __name__ == "__main__":
    main()
