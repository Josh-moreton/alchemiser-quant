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
    poetry run python scripts/trace_strategy_routes.py nova_ibit --out /tmp/nova.json

    # Historical mode (cuts market data at date; no live bar injection)
    poetry run python scripts/trace_strategy_routes.py nova_ibit --as-of 2026-01-06 --out /tmp/nova_2026-01-06.json

    # Toggle partial bar policy to probe Composer semantics
    poetry run python scripts/trace_strategy_routes.py nova_ibit --policy composer
    poetry run python scripts/trace_strategy_routes.py nova_ibit --policy all-live
    poetry run python scripts/trace_strategy_routes.py nova_ibit --policy none-live

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


Policy = Literal["composer", "all-live", "none-live"]
Mode = Literal["live", "historical"]


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


def _make_historical_market_data_adapter(as_of_date: date):
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
        choices=("composer", "all-live", "none-live"),
        default="composer",
        help="Live bar inclusion policy for indicators",
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

    if args.out:
        Path(args.out).write_text(payload)
        print(f"Wrote trace to: {args.out}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
