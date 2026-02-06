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

    # Live mode (uses CachedMarketDataAdapter with completed daily bars from S3)
    poetry run python scripts/trace_strategy_routes.py beam_chain --out /tmp/beam.json

    # Historical mode (cuts market data at date)
    poetry run python scripts/trace_strategy_routes.py beam_chain --as-of 2026-01-06 --out /tmp/beam_2026-01-06.json
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
from typing import Literal
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


Mode = Literal["live", "historical"]


def _parse_date(date_str: str) -> date:
    if date_str.lower() == "yesterday":
        return date.today() - timedelta(days=1)
    if date_str.lower() == "today":
        return date.today()
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def list_strategies() -> list[str]:
    strategies_path = (
        PROJECT_ROOT / "layers" / "shared" / "the_alchemiser" / "shared" / "strategies"
    )
    if not strategies_path.exists():
        return []
    return sorted([p.stem for p in strategies_path.glob("*.clj")])


def _resolve_strategy_file(strategy_name: str) -> tuple[str, Path]:
    strategies_path = (
        PROJECT_ROOT / "layers" / "shared" / "the_alchemiser" / "shared" / "strategies"
    )

    strategy_file = f"{strategy_name}.clj"
    full_path = strategies_path / strategy_file

    if not full_path.exists():
        for p in strategies_path.glob(f"*{strategy_name}*.clj"):
            return p.name, p

    if not full_path.exists():
        raise FileNotFoundError(f"Strategy file not found for: {strategy_name}")

    return strategy_file, full_path


DataSource = Literal["s3", "alpaca"]


@dataclass(frozen=True)
class RunConfig:
    strategy_name: str
    mode: Mode
    as_of: date | None
    data_source: DataSource = "s3"  # Default to S3 for backward compatibility


# Cache for Alpaca daily bars
_ALPACA_DAILY_BARS_CACHE: dict[tuple[str, date], list] = {}


def _fetch_alpaca_daily_bars(symbol: str, as_of_date: date, lookback_days: int = 400) -> list:
    """Fetch daily bars directly from Alpaca API.

    Args:
        symbol: Stock symbol
        as_of_date: End date (inclusive of T-1 data)
        lookback_days: Number of days to look back

    Returns:
        List of bar dicts with open, high, low, close, volume, timestamp
    """
    from alpaca.data.enums import Adjustment
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    cache_key = (symbol, as_of_date)
    if cache_key in _ALPACA_DAILY_BARS_CACHE:
        return _ALPACA_DAILY_BARS_CACHE[cache_key]

    api_key = os.environ.get("ALPACA_API_KEY") or os.environ.get("ALPACA_KEY")
    api_secret = os.environ.get("ALPACA_API_SECRET") or os.environ.get("ALPACA_SECRET")

    if not api_key or not api_secret:
        print(f"  Warning: Alpaca credentials not set, cannot fetch daily bars for {symbol}")
        return []

    try:
        client = StockHistoricalDataClient(api_key, api_secret)

        # Fetch daily bars up to T-1 (day before as_of_date)
        end_date = as_of_date - timedelta(days=1)  # T-1
        start_date = end_date - timedelta(days=lookback_days)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame(1, TimeFrameUnit.Day),
            start=datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc),
            end=datetime(
                end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc
            ),
            adjustment=Adjustment.ALL,
        )

        response = client.get_stock_bars(request)

        bars_data = response.data.get(symbol, []) if hasattr(response, "data") else []
        bars = list(bars_data) if bars_data else []

        result = []
        for bar in bars:
            result.append(
                {
                    "open": Decimal(str(bar.open)),
                    "high": Decimal(str(bar.high)),
                    "low": Decimal(str(bar.low)),
                    "close": Decimal(str(bar.close)),
                    "volume": int(bar.volume),
                    "timestamp": bar.timestamp,
                }
            )

        _ALPACA_DAILY_BARS_CACHE[cache_key] = result
        return result

    except Exception as e:
        print(f"  Warning: Failed to fetch Alpaca daily bars for {symbol}: {e}")
        return []


def _make_alpaca_only_market_data_adapter(as_of_date: date):
    """Create a market data adapter that fetches ONLY from Alpaca API.

    This bypasses the S3 data lake completely and fetches all data directly
    from Alpaca's historical data API.

    Args:
        as_of_date: The historical cutoff date
    """
    from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol

    class AlpacaOnlyMarketDataAdapter(MarketDataPort):
        def __init__(self, cutoff_date: date):
            self.cutoff_date = cutoff_date

        def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
            symbol_str = str(symbol)

            # Fetch daily bars from Alpaca API (up to T-1)
            alpaca_bars = _fetch_alpaca_daily_bars(symbol_str, self.cutoff_date)

            bars: list[BarModel] = []
            for bar_data in alpaca_bars:
                bars.append(
                    BarModel(
                        symbol=symbol_str,
                        timestamp=bar_data["timestamp"],
                        open=bar_data["open"],
                        high=bar_data["high"],
                        low=bar_data["low"],
                        close=bar_data["close"],
                        volume=bar_data["volume"],
                    )
                )

            return bars

        def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
            bars = self.get_bars(symbol, "1D", "1D")
            return bars[-1] if bars else None

        def get_quote(self, symbol: Symbol) -> QuoteModel | None:
            return None

    return AlpacaOnlyMarketDataAdapter(as_of_date)


def _make_historical_market_data_adapter(as_of_date: date):
    """Create a historical market data adapter.

    Uses S3 data lake Parquet files, filtered to the cutoff date.

    Args:
        as_of_date: The historical cutoff date
    """
    import pandas as pd

    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol

    class HistoricalMarketDataAdapter(MarketDataPort):
        def __init__(self, cutoff_date: date):
            self.cutoff_date = cutoff_date
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

            # Filter to bars up to and including the cutoff date.
            # This includes the cutoff date's bar (T-0 semantics), which is correct
            # for post-market-close evaluation when today's completed bar is available.
            cutoff_datetime = pd.Timestamp(self.cutoff_date, tz=timezone.utc)
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
                    )
                )

            return bars

        def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
            bars = self.get_bars(symbol, "1D", "1D")
            return bars[-1] if bars else None

        def get_quote(self, symbol: Symbol) -> QuoteModel | None:
            return None

    return HistoricalMarketDataAdapter(as_of_date)


def run_trace(config: RunConfig) -> dict[str, object]:
    from engines.dsl.engine import DslEngine

    strategy_file, full_path = _resolve_strategy_file(config.strategy_name)

    if config.mode == "live":
        from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter

        market_data_adapter = CachedMarketDataAdapter()
        engine = DslEngine(
            strategy_config_path=full_path.parent,
            market_data_adapter=market_data_adapter,
            debug_mode=True,
        )
    else:
        if config.as_of is None:
            raise ValueError("historical mode requires --as-of")
        # Choose data source adapter
        if config.data_source == "alpaca":
            market_data_adapter = _make_alpaca_only_market_data_adapter(config.as_of)
        else:
            market_data_adapter = _make_historical_market_data_adapter(config.as_of)
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
            "data_source": config.data_source,
            "correlation_id": correlation_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "allocation": allocation_float,
        "allocation_is_100pct_shv": (
            set(allocation_float.keys()) == {"SHV"}
            and abs(allocation_float.get("SHV", 0.0) - 1.0) < 1e-9
        ),
        "decision_path": engine.evaluator.decision_path,
        "debug_traces": engine.evaluator.debug_traces,
        "filter_traces": engine.evaluator.filter_traces,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Trace DSL strategy routes (ifs + filters)")
    parser.add_argument("strategy", nargs="?", help="Strategy name without .clj")
    parser.add_argument("--list", action="store_true", help="List all available strategies")
    parser.add_argument(
        "--as-of", dest="as_of", help="Historical cutoff date (YYYY-MM-DD / today / yesterday)"
    )

    parser.add_argument(
        "--data-source",
        dest="data_source",
        choices=("s3", "alpaca"),
        default="s3",
        help="Data source for historical bars: 's3' (default) uses S3 data lake, 'alpaca' fetches directly from Alpaca API",
    )
    parser.add_argument("--out", help="Write JSON output to this file")

    args = parser.parse_args()

    if args.list:
        for name in list_strategies():
            print(name)
        return

    if not args.strategy:
        parser.error("strategy is required (or use --list)")

    as_of_date = _parse_date(args.as_of) if args.as_of else None
    mode: Mode = "historical" if as_of_date else "live"

    cfg = RunConfig(
        strategy_name=args.strategy,
        mode=mode,
        as_of=as_of_date,
        data_source=args.data_source,
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
