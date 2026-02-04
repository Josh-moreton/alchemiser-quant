#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Test any strategy with all combinations of use_live_bar settings.

For each indicator, use_live_bar=True means include the live date data,
use_live_bar=False means use the previous date only (T-1).

Usage:
    poetry run python scripts/test_strategy_live_bar_combinations.py simons_kmlm
    poetry run python scripts/test_strategy_live_bar_combinations.py bento_collection --workers 16
    poetry run python scripts/test_strategy_live_bar_combinations.py simons_kmlm --expected "TQQQ:0.40,TMF:0.60"

"""

from __future__ import annotations

import argparse
import csv
import os
import re
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
STRATEGIES_PATH = SHARED_LAYER_PATH / "the_alchemiser" / "shared" / "strategies"

sys.path.insert(0, str(STRATEGY_WORKER_PATH))
sys.path.insert(0, str(SHARED_LAYER_PATH))

# Test dates (can be overridden via CLI)
DEFAULT_LIVE_DATE = date(2026, 1, 6)
DEFAULT_HISTORICAL_DATE = date(2026, 1, 5)

# Map of DSL operators to indicator_type names
DSL_TO_INDICATOR_TYPE = {
    "rsi": "rsi",
    "moving-average-price": "moving_average",
    "moving-average-return": "moving_average_return",
    "cumulative-return": "cumulative_return",
    "current-price": "current_price",
    "exponential-moving-average-price": "exponential_moving_average_price",
    "stdev-return": "stdev_return",
    "stdev-price": "stdev_price",
    "max-drawdown": "max_drawdown",
}


def extract_indicators_from_strategy(strategy_file: Path) -> list[str]:
    """Parse a strategy DSL file and extract unique indicator types used."""
    content = strategy_file.read_text()
    
    indicators_found: set[str] = set()
    
    # Look for each DSL operator in the file
    for dsl_op, indicator_type in DSL_TO_INDICATOR_TYPE.items():
        # Match patterns like (rsi ...) or (moving-average-price ...)
        pattern = rf"\({dsl_op}\s+"
        if re.search(pattern, content):
            indicators_found.add(indicator_type)
    
    # Return sorted list for consistent ordering
    return sorted(indicators_found)


@dataclass
class CombinationResult:
    """Result from running a single combination."""

    combination_id: int
    indicator_settings: dict[str, bool]
    allocation: dict[str, float]
    matches_expected: bool
    error: str | None = None

    def to_csv_row(self, indicators: list[str]) -> dict[str, Any]:
        """Convert to CSV row dict."""
        row: dict[str, Any] = {
            "combination_id": self.combination_id,
            "matches_expected": self.matches_expected,
        }
        # Add indicator settings
        for indicator in indicators:
            row[f"{indicator}_live"] = self.indicator_settings.get(indicator, False)

        # Add allocation
        row["allocation"] = (
            "; ".join(f"{k}:{v:.4f}" for k, v in sorted(self.allocation.items()))
            if self.allocation
            else ""
        )
        row["error"] = self.error or ""
        return row


def allocation_matches(alloc: dict[str, float], expected: dict[str, float], tol: float = 0.01) -> bool:
    """Check if allocation matches expected allocation within tolerance."""
    if not expected:
        return False
    if set(alloc.keys()) != set(expected.keys()):
        return False
    for k, v in expected.items():
        if abs(alloc.get(k, 0) - v) > tol:
            return False
    return True


def run_single_combination(args: tuple[int, dict[str, bool], str, str, str]) -> CombinationResult:
    """Run strategy with a specific indicator configuration.
    
    This function runs in a subprocess, so we need to reimport everything.
    """
    import os
    import sys
    from datetime import date, timezone
    from decimal import Decimal
    from pathlib import Path

    import pandas as pd

    combination_id, indicator_settings, strategy_file, live_date_str, historical_date_str = args
    
    # Parse dates
    live_date = date.fromisoformat(live_date_str)
    historical_date = date.fromisoformat(historical_date_str)

    # Re-set paths for subprocess
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    strategy_worker_path = project_root / "functions" / "strategy_worker"
    shared_layer_path = project_root / "layers" / "shared"
    strategies_path = shared_layer_path / "the_alchemiser" / "shared" / "strategies"

    if str(strategy_worker_path) not in sys.path:
        sys.path.insert(0, str(strategy_worker_path))
    if str(shared_layer_path) not in sys.path:
        sys.path.insert(0, str(shared_layer_path))

    os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

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
                        is_incomplete=False,
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

        correlation_id = f"combo-{combination_id}"
        allocation_result, _ = engine.evaluate_strategy(strategy_file, correlation_id)

        allocation = {k: float(v) for k, v in allocation_result.target_weights.items()}

        return CombinationResult(
            combination_id=combination_id,
            indicator_settings=indicator_settings,
            allocation=allocation,
            matches_expected=False,  # Will be checked in main process
        )

    except Exception as e:
        import traceback

        return CombinationResult(
            combination_id=combination_id,
            indicator_settings=indicator_settings,
            allocation={},
            matches_expected=False,
            error=f"{type(e).__name__}: {e}\n{traceback.format_exc()[:500]}",
        )


def generate_all_combinations(indicators: list[str]) -> list[tuple[int, dict[str, bool]]]:
    """Generate all 2^N combinations of indicator settings."""
    combinations = []
    for i, settings in enumerate(product([False, True], repeat=len(indicators))):
        indicator_settings = dict(zip(indicators, settings))
        combinations.append((i, indicator_settings))
    return combinations


def parse_expected_allocation(expected_str: str) -> dict[str, float]:
    """Parse expected allocation string like 'TQQQ:0.40,TMF:0.60'."""
    if not expected_str:
        return {}
    result = {}
    for pair in expected_str.split(","):
        pair = pair.strip()
        if ":" in pair:
            symbol, weight = pair.split(":", 1)
            result[symbol.strip()] = float(weight.strip())
    return result


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test a strategy with all use_live_bar combinations"
    )
    parser.add_argument(
        "strategy",
        type=str,
        help="Strategy name (without .clj extension), e.g., 'simons_kmlm' or 'bento_collection'",
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
        default=None,
        help="Output CSV file (default: <strategy>_live_bar_combinations.csv)",
    )
    parser.add_argument(
        "--expected",
        "-e",
        type=str,
        default="",
        help="Expected allocation, e.g., 'TQQQ:0.40,TMF:0.60' (optional)",
    )
    parser.add_argument(
        "--live-date",
        type=str,
        default=DEFAULT_LIVE_DATE.isoformat(),
        help=f"Live date (use_live_bar=True) in YYYY-MM-DD format (default: {DEFAULT_LIVE_DATE})",
    )
    parser.add_argument(
        "--historical-date",
        type=str,
        default=DEFAULT_HISTORICAL_DATE.isoformat(),
        help=f"Historical date (use_live_bar=False) in YYYY-MM-DD format (default: {DEFAULT_HISTORICAL_DATE})",
    )

    args = parser.parse_args()

    # Validate strategy file exists
    strategy_file = args.strategy
    if not strategy_file.endswith(".clj"):
        strategy_file = f"{strategy_file}.clj"
    
    strategy_path = STRATEGIES_PATH / strategy_file
    if not strategy_path.exists():
        print(f"ERROR: Strategy file not found: {strategy_path}")
        print(f"\nAvailable strategies:")
        for f in STRATEGIES_PATH.glob("*.clj"):
            print(f"  - {f.stem}")
        sys.exit(1)

    # Parse dates
    live_date = date.fromisoformat(args.live_date)
    historical_date = date.fromisoformat(args.historical_date)

    # Extract indicators from strategy
    indicators = extract_indicators_from_strategy(strategy_path)
    if not indicators:
        print(f"ERROR: No indicators found in strategy {strategy_file}")
        sys.exit(1)

    # Parse expected allocation
    expected_allocation = parse_expected_allocation(args.expected)

    # Output file
    output_file = args.output or f"{args.strategy}_live_bar_combinations.csv"

    num_combinations = 2 ** len(indicators)

    print("=" * 80)
    print(f"STRATEGY LIVE BAR COMBINATIONS TEST: {args.strategy}")
    print("=" * 80)
    print(f"Strategy file: {strategy_path.name}")
    print(f"Live date (use_live_bar=True):     {live_date}")
    print(f"Historical date (use_live_bar=False): {historical_date}")
    print(f"Indicators found: {indicators}")
    print(f"Total combinations: 2^{len(indicators)} = {num_combinations}")
    if expected_allocation:
        print(f"Expected allocation: {expected_allocation}")
    print(f"Workers: {args.workers}")
    print(f"Output: {output_file}")
    print("=" * 80)

    combinations = generate_all_combinations(indicators)
    print(f"\nGenerated {len(combinations)} combinations")

    # Prepare args for subprocess (need to pass serializable data)
    combo_args = [
        (combo_id, settings, strategy_file, live_date.isoformat(), historical_date.isoformat())
        for combo_id, settings in combinations
    ]

    results: list[CombinationResult] = []
    start_time = datetime.now()

    print(f"\nRunning {len(combinations)} combinations with {args.workers} workers...")
    print()

    completed = 0
    matches_found = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(run_single_combination, combo_arg): combo_arg[0]
            for combo_arg in combo_args
        }

        for future in as_completed(futures):
            combo_id = futures[future]
            try:
                result = future.result()
                
                # Check if matches expected
                if expected_allocation:
                    result.matches_expected = allocation_matches(
                        result.allocation, expected_allocation
                    )
                
                results.append(result)
                completed += 1

                if result.matches_expected:
                    matches_found += 1
                    settings_str = ", ".join(
                        f"{k}={'T' if v else 'F'}"
                        for k, v in result.indicator_settings.items()
                    )
                    print(f"✓ MATCH #{matches_found} (combo {combo_id}): {settings_str}")

                # Progress update
                update_interval = max(1, num_combinations // 20)
                if completed % update_interval == 0 or completed == len(combinations):
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = completed / elapsed if elapsed > 0 else 0
                    remaining = (len(combinations) - completed) / rate if rate > 0 else 0
                    print(
                        f"  Progress: {completed}/{len(combinations)} "
                        f"({100*completed/len(combinations):.1f}%) - "
                        f"{rate:.1f}/sec - ETA: {remaining:.0f}s"
                        + (f" - Matches: {matches_found}" if expected_allocation else "")
                    )

            except Exception as e:
                print(f"  ERROR combo {combo_id}: {e}")
                results.append(
                    CombinationResult(
                        combination_id=combo_id,
                        indicator_settings=combinations[combo_id][1],
                        allocation={},
                        matches_expected=False,
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
    output_path = PROJECT_ROOT / output_file
    fieldnames = (
        ["combination_id", "matches_expected"]
        + [f"{ind}_live" for ind in indicators]
        + ["allocation", "error"]
    )

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_csv_row(indicators))

    print(f"\nResults written to: {output_path}")

    # Summary
    matching = [r for r in results if r.matches_expected]
    errors = [r for r in results if r.error]

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total combinations tested: {len(results)}")
    if expected_allocation:
        print(f"Matching expected allocation: {len(matching)}")
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
        for r in errors[:5]:
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
        is_expected = False
        if expected_allocation:
            expected_key = "; ".join(f"{k}:{v:.4f}" for k, v in sorted(expected_allocation.items()))
            is_expected = alloc == expected_key
        marker = "✓" if is_expected else " "
        print(f"  {marker} {alloc} ({len(combo_ids)} combos: {combo_ids})")


if __name__ == "__main__":
    main()
