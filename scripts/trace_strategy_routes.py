#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Route tracing script for DSL strategies (Composer parity debugging).

Captures:
- Final allocation
- Decision path (if branches)
- Debug traces (comparisons)
- Filter traces (ranking + selected candidates)

This is specifically useful for diagnosing cases where Composer selects a
risk-off `SHV` route but our engine selects a bucket of assets (or vice versa).

Usage:
    poetry run python scripts/trace_strategy_routes.py --list

    # Live mode (uses CachedMarketDataAdapter; optional live bar injection)
    poetry run python scripts/trace_strategy_routes.py beam_chain --out /tmp/beam.json

    # Historical mode (cuts market data at date; no live bar injection)
    poetry run python scripts/trace_strategy_routes.py beam_chain --as-of 2026-01-06 --out /tmp/beam_2026-01-06.json

    # Toggle partial bar policy to probe Composer semantics
    poetry run python scripts/trace_strategy_routes.py beam_chain --policy composer
    poetry run python scripts/trace_strategy_routes.py beam_chain --policy all-live
    poetry run python scripts/trace_strategy_routes.py beam_chain --policy none-live

"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable, Literal
from uuid import UUID

from dotenv import load_dotenv

# Load environment variables from .env (for Alpaca credentials, etc.)
load_dotenv()

# Set environment variables for S3 market data access
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

PROJECT_ROOT = Path(__file__).parent.parent

# Add functions/strategy_worker to path for imports
sys.path.insert(0, str(PROJECT_ROOT / "functions" / "strategy_worker"))

# Add layers/shared to path for shared imports
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))


Policy = Literal["composer", "all-live", "none-live", "custom"]
Mode = Literal["live", "historical"]

# Global per-indicator override map (set via --indicator-config or programmatically)
_INDICATOR_OVERRIDES: dict[str, bool] = {}


def set_indicator_overrides(overrides: dict[str, bool]) -> None:
    """Set per-indicator live bar overrides programmatically.
    
    Args:
        overrides: Dict mapping indicator_type to use_live_bar boolean.
                   e.g., {"rsi": True, "cumulative_return": False}
    """
    global _INDICATOR_OVERRIDES
    _INDICATOR_OVERRIDES = dict(overrides)


def _parse_date(date_str: str) -> date:
    if date_str.lower() == "yesterday":
        return date.today() - timedelta(days=1)
    if date_str.lower() == "today":
        return date.today()
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def list_strategies() -> list[str]:
    strategies_path = PROJECT_ROOT / "layers" / "shared" / "the_alchemiser" / "shared" / "strategies"
    if not strategies_path.exists():
        return []
    return sorted([p.stem for p in strategies_path.glob("*.clj")])


def _resolve_strategy_file(strategy_name: str) -> tuple[str, Path]:
    strategies_path = PROJECT_ROOT / "layers" / "shared" / "the_alchemiser" / "shared" / "strategies"

    strategy_file = f"{strategy_name}.clj"
    full_path = strategies_path / strategy_file

    if not full_path.exists():
        for p in strategies_path.glob(f"*{strategy_name}*.clj"):
            return p.name, p

    if not full_path.exists():
        raise FileNotFoundError(f"Strategy file not found for: {strategy_name}")

    return strategy_file, full_path


def _apply_live_bar_policy(policy: Policy) -> None:
    """Override live-bar inclusion policy inside IndicatorService.

    IndicatorService imports `should_use_live_bar` at module import time, so we
    patch the function in that module namespace.
    """

    import indicators.indicator_service as indicator_service_mod

    if policy == "composer":
        # Default behavior: defer to shared partial_bar_config.should_use_live_bar
        from the_alchemiser.shared.indicators.partial_bar_config import should_use_live_bar

        indicator_service_mod.should_use_live_bar = should_use_live_bar
        return

    if policy == "custom":
        # Use per-indicator overrides from _INDICATOR_OVERRIDES, falling back to config
        from the_alchemiser.shared.indicators.partial_bar_config import should_use_live_bar as default_fn

        def _custom_should_use_live_bar(indicator_type: str) -> bool:
            if indicator_type in _INDICATOR_OVERRIDES:
                return _INDICATOR_OVERRIDES[indicator_type]
            return default_fn(indicator_type)

        indicator_service_mod.should_use_live_bar = _custom_should_use_live_bar
        return

    def _always(_indicator_type: str) -> bool:
        return True

    def _never(_indicator_type: str) -> bool:
        return False

    if policy == "all-live":
        indicator_service_mod.should_use_live_bar = _always
        return

    if policy == "none-live":
        indicator_service_mod.should_use_live_bar = _never
        return

    raise ValueError(f"Unknown policy: {policy}")


@dataclass(frozen=True)
class RunConfig:
    strategy_name: str
    mode: Mode
    policy: Policy
    append_live_bar: bool
    as_of: date | None


def _fetch_simulated_live_bar(symbol: str, as_of_date: date) -> dict[str, Decimal] | None:
    """Fetch the 3:45 PM ET 15-minute candle close as simulated live bar.
    
    This fetches the 15-minute bar that closes at 3:45 PM Eastern Time on the
    given date. This simulates the "live" bar that Composer would see if running
    the strategy at that time.
    
    Args:
        symbol: Stock symbol to fetch
        as_of_date: The historical date to get the 3:45 PM bar for
        
    Returns:
        Dict with bar data (open, high, low, close, volume) or None if not available
    """
    import pytz
    from alpaca.data.enums import Adjustment
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    
    # Try both naming conventions for Alpaca credentials
    api_key = os.environ.get("ALPACA_API_KEY") or os.environ.get("ALPACA_KEY")
    api_secret = os.environ.get("ALPACA_API_SECRET") or os.environ.get("ALPACA_SECRET")
    
    if not api_key or not api_secret:
        print(f"  Warning: Alpaca credentials not set, cannot fetch simulated live bar for {symbol}")
        return None
    
    try:
        client = StockHistoricalDataClient(api_key, api_secret)
        
        # 3:45 PM ET is the close of the 15-minute bar starting at 3:30 PM
        # In UTC: 3:45 PM ET = 8:45 PM UTC (EST) or 7:45 PM UTC (EDT)
        et_tz = pytz.timezone("America/New_York")
        
        # Create 3:30 PM ET datetime for the target date (bar start time)
        bar_start_et = et_tz.localize(datetime(as_of_date.year, as_of_date.month, as_of_date.day, 15, 30, 0))
        bar_end_et = et_tz.localize(datetime(as_of_date.year, as_of_date.month, as_of_date.day, 15, 45, 0))
        
        # Convert to UTC for Alpaca API
        bar_start_utc = bar_start_et.astimezone(pytz.UTC)
        bar_end_utc = bar_end_et.astimezone(pytz.UTC)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame(15, TimeFrameUnit.Minute),
            start=bar_start_utc,
            end=bar_end_utc + timedelta(minutes=1),  # Small buffer to ensure we get the bar
            adjustment=Adjustment.ALL,
        )
        
        response = client.get_stock_bars(request)
        
        # Access bars via .data dict (BarSet response structure)
        bars_data = response.data.get(symbol, []) if hasattr(response, 'data') else []
        bars = list(bars_data) if bars_data else []
        
        if not bars:
            return None
        
        # Take the FIRST bar (the one starting at 3:30 PM that closes at 3:45 PM)
        bar = bars[0]
        return {
            "open": Decimal(str(bar.open)),
            "high": Decimal(str(bar.high)),
            "low": Decimal(str(bar.low)),
            "close": Decimal(str(bar.close)),
            "volume": int(bar.volume),
            "timestamp": bar.timestamp,
        }
        
    except Exception as e:
        print(f"  Warning: Failed to fetch simulated live bar for {symbol}: {e}")
        return None


# Cache for simulated live bars to avoid repeated API calls
_SIMULATED_LIVE_BAR_CACHE: dict[tuple[str, date], dict[str, Decimal] | None] = {}


def _get_simulated_live_bar_cached(symbol: str, as_of_date: date) -> dict[str, Decimal] | None:
    """Get simulated live bar with caching."""
    cache_key = (symbol, as_of_date)
    if cache_key not in _SIMULATED_LIVE_BAR_CACHE:
        _SIMULATED_LIVE_BAR_CACHE[cache_key] = _fetch_simulated_live_bar(symbol, as_of_date)
    return _SIMULATED_LIVE_BAR_CACHE[cache_key]


def _make_historical_market_data_adapter(as_of_date: date, simulate_live_bar: bool = True):
    """Create a historical market data adapter.
    
    Args:
        as_of_date: The historical cutoff date
        simulate_live_bar: If True, append a simulated live bar using the 3:45 PM ET
                          15-minute candle from Alpaca. This bar will be marked as
                          is_incomplete=True so the indicator service can choose
                          whether to include or exclude it based on indicator config.
    """
    import pandas as pd

    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol

    class HistoricalMarketDataAdapter(MarketDataPort):
        def __init__(self, cutoff_date: date, inject_live_bar: bool):
            self.cutoff_date = cutoff_date
            self.inject_live_bar = inject_live_bar
            self.market_data_store = MarketDataStore()
            self._cache: dict[str, pd.DataFrame] = {}

        def _get_dataframe(self, symbol: str) -> pd.DataFrame:
            if symbol not in self._cache:
                df = self.market_data_store.read_symbol_data(symbol)
                if df is None or df.empty:
                    self._cache[symbol] = pd.DataFrame()
                else:
                    if "timestamp" in df.columns:
                        df = df.set_index("timestamp")
                    if not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index)
                    self._cache[symbol] = df
            return self._cache[symbol]

        def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
            symbol_str = str(symbol)
            df = self._get_dataframe(symbol_str)
            if df.empty:
                return []

            # Use day BEFORE cutoff for daily bars (T-1 data)
            # The simulated live bar will provide T0 data if configured
            cutoff_datetime = pd.Timestamp(self.cutoff_date - timedelta(days=1), tz=timezone.utc)
            if df.index.tz is None:
                df.index = df.index.tz_localize(timezone.utc)

            df_filtered = df[df.index.normalize() <= cutoff_datetime]
            if df_filtered.empty:
                return []

            bars: list[BarModel] = []
            for ts, row in df_filtered.iterrows():
                bars.append(
                    BarModel(
                        symbol=symbol_str,
                        timestamp=ts.to_pydatetime(),
                        open=Decimal(str(row.get("open", row.get("Open", 0)))),
                        high=Decimal(str(row.get("high", row.get("High", 0)))),
                        low=Decimal(str(row.get("low", row.get("Low", 0)))),
                        close=Decimal(str(row.get("close", row.get("Close", 0)))),
                        volume=int(row.get("volume", row.get("Volume", 0))),
                        is_incomplete=False,
                    )
                )
            
            # Append simulated live bar if configured
            if self.inject_live_bar:
                live_bar_data = _get_simulated_live_bar_cached(symbol_str, self.cutoff_date)
                if live_bar_data:
                    # Create a "live" bar with is_incomplete=True
                    # This allows the indicator service to respect should_use_live_bar()
                    live_bar = BarModel(
                        symbol=symbol_str,
                        timestamp=live_bar_data["timestamp"],
                        open=live_bar_data["open"],
                        high=live_bar_data["high"],
                        low=live_bar_data["low"],
                        close=live_bar_data["close"],
                        volume=live_bar_data["volume"],
                        is_incomplete=True,  # Mark as live/partial bar
                    )
                    bars.append(live_bar)
            
            return bars

        def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
            bars = self.get_bars(symbol, "1D", "1D")
            return bars[-1] if bars else None

        def get_quote(self, symbol: Symbol) -> QuoteModel | None:
            return None

    return HistoricalMarketDataAdapter(as_of_date, simulate_live_bar)


def run_trace(config: RunConfig) -> dict[str, object]:
    from engines.dsl.engine import DslEngine

    strategy_file, full_path = _resolve_strategy_file(config.strategy_name)

    _apply_live_bar_policy(config.policy)

    if config.mode == "live":
        from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter

        market_data_adapter = CachedMarketDataAdapter(append_live_bar=config.append_live_bar)
        engine = DslEngine(
            strategy_config_path=full_path.parent,
            market_data_adapter=market_data_adapter,
            debug_mode=True,
        )
    else:
        if config.as_of is None:
            raise ValueError("historical mode requires --as-of")
        # Always inject simulated live bar - the indicator service will decide
        # whether to use or strip it based on should_use_live_bar() per indicator
        market_data_adapter = _make_historical_market_data_adapter(config.as_of, simulate_live_bar=True)
        engine = DslEngine(
            strategy_config_path=full_path.parent,
            market_data_adapter=market_data_adapter,
            debug_mode=True,
        )

    correlation_id = f"route-trace-{config.strategy_name}-{datetime.now(timezone.utc).isoformat()}"
    allocation, _trace = engine.evaluate_strategy(strategy_file, correlation_id)

    allocation_float = {k: float(v) for k, v in allocation.target_weights.items()}

    return {
        "meta": {
            "strategy_name": config.strategy_name,
            "strategy_file": strategy_file,
            "mode": config.mode,
            "as_of": config.as_of.isoformat() if config.as_of else None,
            "append_live_bar": config.append_live_bar,
            "policy": config.policy,
            "correlation_id": correlation_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "allocation": allocation_float,
        "allocation_is_100pct_shv": (set(allocation_float.keys()) == {"SHV"} and abs(allocation_float.get("SHV", 0.0) - 1.0) < 1e-9),
        "decision_path": engine.evaluator.decision_path,
        "debug_traces": engine.evaluator.debug_traces,
        "filter_traces": engine.evaluator.filter_traces,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Trace DSL strategy routes (ifs + filters)")
    parser.add_argument("strategy", nargs="?", help="Strategy name without .clj")
    parser.add_argument("--list", action="store_true", help="List all available strategies")
    parser.add_argument("--as-of", dest="as_of", help="Historical cutoff date (YYYY-MM-DD / today / yesterday)")
    parser.add_argument(
        "--policy",
        choices=("composer", "all-live", "none-live", "custom"),
        default="composer",
        help="Live bar inclusion policy for indicators",
    )
    parser.add_argument(
        "--indicator-config",
        dest="indicator_config",
        help="JSON file or string with per-indicator overrides, e.g., '{\"rsi\": true, \"cumulative_return\": false}'",
    )
    parser.add_argument(
        "--append-live-bar",
        dest="append_live_bar",
        action="store_true",
        default=True,
        help="(live mode) append today’s partial bar when available",
    )
    parser.add_argument(
        "--no-append-live-bar",
        dest="append_live_bar",
        action="store_false",
        help="(live mode) disable partial bar injection",
    )
    parser.add_argument("--out", help="Write JSON output to this file")

    args = parser.parse_args()

    if args.list:
        for name in list_strategies():
            print(name)
        return

    if not args.strategy:
        parser.error("strategy is required (or use --list)")

    # Parse and apply per-indicator config if provided
    if args.indicator_config:
        indicator_config_str = args.indicator_config
        # Check if it's a file path
        config_path = Path(indicator_config_str)
        if config_path.exists():
            indicator_config_str = config_path.read_text()
        try:
            indicator_overrides = json.loads(indicator_config_str)
            set_indicator_overrides(indicator_overrides)
            # Auto-switch to custom policy if not already set
            if args.policy == "composer":
                args.policy = "custom"
        except json.JSONDecodeError as e:
            parser.error(f"Invalid JSON in --indicator-config: {e}")

    as_of_date = _parse_date(args.as_of) if args.as_of else None
    mode: Mode = "historical" if as_of_date else "live"

    cfg = RunConfig(
        strategy_name=args.strategy,
        mode=mode,
        policy=args.policy,
        append_live_bar=bool(args.append_live_bar),
        as_of=as_of_date,
    )

    result = run_trace(cfg)
    def _json_default(obj: object) -> str:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return str(obj)

    payload = json.dumps(result, indent=2, sort_keys=False, default=_json_default)

    if args.out == "stdout" or args.out == "json":
        # Output JSON to stdout (for subprocess consumption)
        print(payload)
    elif args.out:
        Path(args.out).write_text(payload)
        print(f"Wrote trace to: {args.out}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
