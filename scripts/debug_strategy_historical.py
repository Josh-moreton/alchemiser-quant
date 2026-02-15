#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Debug script for running a strategy with historical market data cutoff.

This script runs a strategy using market data up to a specific date,
allowing us to verify what signals would have been generated on a past date.

Usage:
    poetry run python scripts/debug_strategy_historical.py simons_kmlm --as-of 2026-01-06
    poetry run python scripts/debug_strategy_historical.py simons_kmlm --as-of yesterday

"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

# Set environment variables for S3 market data access and DynamoDB group cache
os.environ.setdefault("MARKET_DATA_BUCKET", "alch-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("GROUP_HISTORY_TABLE", "alch-dev-group-history")

# Add functions/strategy_worker to path for imports
strategy_worker_path = Path(__file__).parent.parent / "functions" / "strategy_worker"
sys.path.insert(0, str(strategy_worker_path))

# Add shared_layer/python to path for shared imports (Lambda layer convention)
shared_layer_path = Path(__file__).parent.parent / "shared_layer" / "python"
sys.path.insert(0, str(shared_layer_path))

if TYPE_CHECKING:
    import pandas as pd
    from the_alchemiser.shared.types.market_data import BarModel
    from the_alchemiser.shared.value_objects.symbol import Symbol


def parse_date(date_str: str) -> date:
    """Parse date string to date object.
    
    Args:
        date_str: Date string like "2026-01-06", "yesterday", "today"
        
    Returns:
        Parsed date object
    """
    if date_str.lower() == "yesterday":
        return date.today() - timedelta(days=1)
    if date_str.lower() == "today":
        return date.today()
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def run_strategy_as_of(strategy_name: str, as_of_date: date) -> dict:
    """Run a strategy with market data cutoff at a specific date.
    
    Args:
        strategy_name: Name of strategy (without .clj extension)
        as_of_date: Only use market data up to and including this date
        
    Returns:
        Dictionary with allocation results
    """
    import pandas as pd
    
    # Import after path setup
    from engines.dsl.engine import DslEngine

    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.types.market_data import BarModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol
    
    strategies_path = shared_layer_path / "the_alchemiser" / "shared" / "strategies"
    
    # Find strategy file
    strategy_file = f"{strategy_name}.clj"
    full_path = strategies_path / strategy_file
    
    if not full_path.exists():
        # Try with prefix numbers
        for f in strategies_path.glob(f"*{strategy_name}*.clj"):
            strategy_file = f.name
            full_path = f
            break
    
    if not full_path.exists():
        raise FileNotFoundError(f"Strategy file not found: {strategy_name}")
    
    print(f"\n{'=' * 60}")
    print(f"Running strategy: {strategy_file}")
    print(f"As-of date: {as_of_date} (market data cutoff)")
    print(f"{'=' * 60}\n")
    
    # Create a wrapper adapter that filters data by date
    class HistoricalMarketDataAdapter(MarketDataPort):
        """Adapter that returns market data up to a cutoff date."""
        
        def __init__(self, cutoff_date: date):
            self.cutoff_date = cutoff_date
            self.market_data_store = MarketDataStore()
            self._cache: dict[str, pd.DataFrame] = {}
            
        def _get_dataframe(self, symbol: str) -> pd.DataFrame:
            """Get DataFrame for symbol, cached."""
            if symbol not in self._cache:
                df = self.market_data_store.read_symbol_data(symbol)
                if df is not None and not df.empty:
                    # Ensure we have a proper datetime index
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
            """Get bars filtered to cutoff date.
            
            This is the main method used by the indicator service.
            """
            symbol_str = str(symbol)
            df = self._get_dataframe(symbol_str)
            
            if df.empty:
                return []
            
            # Filter to cutoff date
            cutoff_datetime = pd.Timestamp(self.cutoff_date, tz=timezone.utc)
            
            # Normalize index to date for comparison
            if df.index.tz is None:
                df.index = df.index.tz_localize(timezone.utc)
            
            df_filtered = df[df.index.normalize() <= cutoff_datetime]
            
            if df_filtered.empty:
                return []
            
            # Convert to BarModel list
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
        
        def get_last_date(self, symbol: str) -> date | None:
            """Get last available date for symbol (up to cutoff)."""
            bars = self.get_bars(Symbol(symbol), "1D", "1D")
            if not bars:
                return None
            return bars[-1].timestamp.date()
    
    # Create adapter with cutoff
    market_data_adapter = HistoricalMarketDataAdapter(as_of_date)
    
    # Check what date the data actually goes up to for key symbols
    print("Data cutoff verification:")
    for symbol_str in ["SPY", "TLT", "SQQQ", "XLK", "KMLM"]:
        try:
            last_date = market_data_adapter.get_last_date(symbol_str)
            if last_date:
                print(f"  {symbol_str}: last bar = {last_date}")
            else:
                print(f"  {symbol_str}: no data")
        except Exception as e:
            print(f"  {symbol_str}: error - {e}")
    print()
    
    # Create DSL engine with debug mode and our historical adapter
    engine = DslEngine(
        strategy_config_path=strategies_path,
        market_data_adapter=market_data_adapter,
        debug_mode=True,
    )
    
    # Evaluate strategy
    correlation_id = f"debug-historical-{strategy_name}"
    allocation, trace = engine.evaluate_strategy(strategy_file, correlation_id)
    
    # Collect debug traces
    debug_traces = engine.evaluator.debug_traces
    
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    print(f"\nTarget Allocation (as of {as_of_date}):")
    for symbol, weight in allocation.target_weights.items():
        print(f"  {symbol}: {weight:.4f}")
    
    print(f"\nTotal Weight: {sum(allocation.target_weights.values()):.4f}")
    
    # Show key debug traces
    if debug_traces:
        print("\n" + "=" * 60)
        print("KEY CONDITION EVALUATIONS")
        print("=" * 60)
        
        for i, trace_entry in enumerate(debug_traces, 1):
            left = trace_entry.get("left_expr", "?")
            left_val = trace_entry.get("left_value", "?")
            op = trace_entry.get("operator", "?")
            right = trace_entry.get("right_expr", "?")
            right_val = trace_entry.get("right_value", "?")
            result = trace_entry.get("result", "?")
            
            print(f"\n[{i}] {left} {op} {right}")
            print(f"    Values: {left_val} {op} {right_val}")
            print(f"    Result: {result}")
    
    return {
        "allocation": {k: float(v) for k, v in allocation.target_weights.items()},
        "as_of_date": str(as_of_date),
        "debug_traces": debug_traces,
    }


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Debug a strategy with historical market data cutoff"
    )
    parser.add_argument(
        "strategy",
        help="Strategy name (without .clj extension)",
    )
    parser.add_argument(
        "--as-of",
        required=True,
        dest="as_of",
        help="Date cutoff for market data (YYYY-MM-DD, 'yesterday', or 'today')",
    )
    
    args = parser.parse_args()
    
    try:
        as_of_date = parse_date(args.as_of)
        result = run_strategy_as_of(args.strategy, as_of_date)
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Strategy: {args.strategy}")
        print(f"As-of date: {as_of_date}")
        print(f"Result: {list(result['allocation'].keys())}")
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
