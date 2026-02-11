#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Backfill DynamoDB group cache for all named groups in a .clj strategy file.

Parses the strategy file, discovers all ``(group "Name" ...)`` nodes,
evaluates each group's AST body for every trading day in the lookback
window, computes weighted portfolio daily returns, writes them to the
``GroupHistoricalSelectionsTable`` in DynamoDB, and prints a summary
report of what was uploaded.

Performance optimisations:
    - All market data is pre-loaded into memory before evaluation begins,
      eliminating per-bar S3 metadata validation round-trips.
    - DynamoDB writes are batched (25 items per request) instead of
      individual put_item calls.
    - Groups at the same nesting depth are processed in parallel using
      fork-based multiprocessing (``--parallel N``).
    - Depth-level passes process deepest groups first so that outer
      groups can rely on completed inner-group caches.

Usage:
    poetry run python scripts/backfill_group_cache.py \\
        layers/shared/the_alchemiser/shared/strategies/ftl_starburst.clj

    # Custom lookback (default 45 calendar days):
    poetry run python scripts/backfill_group_cache.py \\
        ftl_starburst.clj --days 60

    # Backfill ALL available history (as far back as data exists):
    poetry run python scripts/backfill_group_cache.py \\
        ftl_starburst.clj --all

    # Dry-run (compute but do not write to DynamoDB):
    poetry run python scripts/backfill_group_cache.py \\
        ftl_starburst.clj --dry-run

    # Target specific group(s):
    poetry run python scripts/backfill_group_cache.py \\
        ftl_starburst.clj --group "WYLD Mean Reversion*"

    # Parallel processing (4 workers):
    poetry run python scripts/backfill_group_cache.py \\
        ftl_starburst.clj --parallel 4

    # Process only a specific depth level:
    poetry run python scripts/backfill_group_cache.py \\
        ftl_starburst.clj --level 2
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import sys
import time
import uuid
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
# macOS: prevent fork-safety crashes in child processes when the parent has
# already initialised Apple networking frameworks (boto3/S3 preload).
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("GROUP_HISTORY_TABLE", "alchemiser-dev-group-history")

# ---------------------------------------------------------------------------
# Path setup -- use shared _setup_imports for layer path, then add the
# strategy_worker function directory for engines.* imports.
# ---------------------------------------------------------------------------
import _setup_imports  # noqa: F401

PROJECT_ROOT = _setup_imports.PROJECT_ROOT
STRATEGY_WORKER_PATH = PROJECT_ROOT / "functions" / "strategy_worker"
STRATEGIES_DIR = (
    _setup_imports.SHARED_LAYER_PATH / "the_alchemiser" / "shared" / "strategies"
)

sys.path.insert(0, str(STRATEGY_WORKER_PATH))

# Deep nesting in FTL Starburst etc.
sys.setrecursionlimit(10000)

# ---------------------------------------------------------------------------
# Indicator warm-up period
# ---------------------------------------------------------------------------
# Many indicators need a minimum amount of historical data before they can
# produce valid results. For example:
#   - max_drawdown needs at least 12 bars
#   - moving averages (e.g., SMA 200) need 200 bars
#   - RSI typically needs 14+ bars
#
# We add this buffer (in trading days) to the earliest available date to
# ensure indicators have enough data to calculate properly.
INDICATOR_WARMUP_DAYS = 90  # ~3 months of trading days for safety

# ---------------------------------------------------------------------------
# Terminal colours (ANSI)
# ---------------------------------------------------------------------------
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


# We import _derive_group_id from the actual portfolio module (after
# path setup) to guarantee identical cache keys. See backfill_strategy_groups().


# ---------------------------------------------------------------------------
# Module-level shared state for parallel workers (set before fork)
# ---------------------------------------------------------------------------
_WORKER_STATE: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Data class for discovered groups
# ---------------------------------------------------------------------------
class GroupInfo:
    """Metadata about a discovered group that needs backfilling."""

    __slots__ = ("name", "body", "depth", "parent_filter_metric")

    def __init__(
        self,
        name: str,
        body: list[Any],
        depth: int,
        parent_filter_metric: str,
    ) -> None:
        self.name = name
        self.body = body
        self.depth = depth
        self.parent_filter_metric = parent_filter_metric

    def __repr__(self) -> str:
        return (
            f"GroupInfo(name={self.name!r}, depth={self.depth}, "
            f"metric={self.parent_filter_metric!r})"
        )


# ---------------------------------------------------------------------------
# AST walking -- discover groups that are children of filter operators
# ---------------------------------------------------------------------------
def _find_filter_targeted_groups(
    node: Any,
    depth: int = 0,
) -> list[GroupInfo]:
    """Walk AST and find groups that are direct children of ``filter`` operators.

    Only these groups need cached PnL data because the filter needs to
    compute a metric (moving-average-return, stdev-return, etc.) over
    their historical return stream to rank/select them.

    Groups that are just structural containers (e.g. ``(group "Bull" ...)``
    nested inside an ``if`` branch) do NOT need caching -- they resolve
    to a single allocation and their PnL is never queried by a filter.

    Within each filter-targeted group, we also recurse to find any
    inner filter-targeted groups (e.g. "MAX DD: TQQQ vs UVXY" inside
    "WYLD...") since those inner filters also need cached PnL for
    their own group children.

    Args:
        node: AST node to walk.
        depth: Current nesting depth (0 = top-level).

    Returns:
        List of GroupInfo with name, body, depth, and parent metric.

    """
    from the_alchemiser.shared.schemas.ast_node import ASTNode

    results: list[GroupInfo] = []
    if not isinstance(node, ASTNode):
        return results

    if not node.is_list() or not node.children:
        return results

    first = node.children[0]

    # Check if this is a (filter ...) node
    if first.is_symbol() and first.get_symbol_name() == "filter":
        # Extract the metric name from the condition expression
        metric_name = _extract_metric_name(node.children[1] if len(node.children) > 1 else None)

        # The portfolio list is the last argument (args[2] with selection, args[1] without)
        portfolio_node = node.children[-1] if len(node.children) >= 3 else None

        if portfolio_node is not None:
            # The portfolio list is a vector [...] which is parsed as a list node
            portfolio_items: list[ASTNode] = []
            if portfolio_node.is_list():
                # Could be a vector of items or a single item
                portfolio_items = list(portfolio_node.children)
            else:
                portfolio_items = [portfolio_node]

            # Find group nodes among the portfolio items
            for item in portfolio_items:
                if not isinstance(item, ASTNode) or not item.is_list():
                    continue
                if not item.children:
                    continue
                item_first = item.children[0]
                if (
                    item_first.is_symbol()
                    and item_first.get_symbol_name() == "group"
                    and len(item.children) >= 3
                ):
                    name_node = item.children[1]
                    name_val = name_node.get_atom_value()
                    if isinstance(name_val, str):
                        body = list(item.children[2:])
                        results.append(GroupInfo(
                            name=name_val,
                            body=body,
                            depth=depth,
                            parent_filter_metric=metric_name,
                        ))
                        # Recurse into this group's body to find inner
                        # filter-targeted groups at depth+1
                        for body_expr in body:
                            results.extend(
                                _find_filter_targeted_groups(body_expr, depth + 1)
                            )

    # Always recurse into all children to find filters at any level
    for child in node.children:
        # Skip the portfolio_items we already processed above
        if first.is_symbol() and first.get_symbol_name() == "filter":
            # For filter nodes, we already recursed into group bodies above.
            # But we still need to recurse into the condition and selection
            # expressions (unlikely to contain filters, but be thorough).
            if child is not node.children[-1]:
                results.extend(_find_filter_targeted_groups(child, depth))
        else:
            results.extend(_find_filter_targeted_groups(child, depth))

    return results


def _extract_metric_name(condition_node: Any) -> str:
    """Extract the metric name from a filter condition AST node.

    E.g. ``(moving-average-return {:window 10})`` -> ``"moving-average-return"``
    """
    from the_alchemiser.shared.schemas.ast_node import ASTNode

    if not isinstance(condition_node, ASTNode):
        return "unknown"
    if condition_node.is_symbol():
        return condition_node.get_symbol_name() or "unknown"
    if condition_node.is_list() and condition_node.children:
        first = condition_node.children[0]
        if first.is_symbol():
            return first.get_symbol_name() or "unknown"
    return "unknown"


# ---------------------------------------------------------------------------
# In-memory market data adapter (zero I/O after pre-load)
# ---------------------------------------------------------------------------
class _InMemoryAdapter:
    """Market data adapter serving from pre-loaded in-memory DataFrames.

    All data is loaded upfront into a dict of DataFrames. Bar lookups
    are converted once per symbol and cached as BarModel lists.  This
    eliminates ALL S3 metadata validation and network I/O during the
    evaluation phase.
    """

    def __init__(self, dataframes: dict[str, pd.DataFrame]) -> None:
        self._data = dataframes
        self._bar_cache: dict[str, list[Any]] = {}

    def get_bars(
        self,
        symbol: Any,
        period: str,  # noqa: ARG002 - always return all bars
        timeframe: str,  # noqa: ARG002
    ) -> list[Any]:
        """Return all bars for a symbol from the in-memory cache.

        Period filtering is ignored -- the indicator service's as_of_date
        handles point-in-time truncation.  Returning all bars ensures
        indicators have the full history they need.
        """
        from the_alchemiser.shared.types.market_data import BarModel

        sym = str(symbol)
        if sym in self._bar_cache:
            return self._bar_cache[sym]

        df = self._data.get(sym)
        if df is None or df.empty:
            self._bar_cache[sym] = []
            return []

        # Convert DataFrame to BarModel list once and cache
        df = df.copy()
        if "timestamp" not in df.columns:
            self._bar_cache[sym] = []
            return []

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp")

        bars: list[BarModel] = []
        for row in df.itertuples(index=False):
            ts = row.timestamp
            if isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
            bars.append(
                BarModel(
                    symbol=sym,
                    timestamp=ts,
                    open=Decimal(str(row.open)),
                    high=Decimal(str(row.high)),
                    low=Decimal(str(row.low)),
                    close=Decimal(str(row.close)),
                    volume=int(row.volume),
                )
            )

        self._bar_cache[sym] = bars
        return bars

    def get_latest_bar(self, symbol: Any) -> Any:
        """Return the most recent bar."""
        bars = self.get_bars(symbol, "MAX", "1Day")
        return bars[-1] if bars else None

    def get_quote(self, symbol: Any) -> Any:
        """Not needed for backfill."""
        return None


# ---------------------------------------------------------------------------
# Pre-load all market data into memory
# ---------------------------------------------------------------------------
def _preload_all_market_data(symbols: set[str]) -> dict[str, pd.DataFrame]:
    """Download all symbol data from S3 and load into memory.

    Each symbol's parquet file is fetched once from S3 (with local cache).
    After this call, no further S3 I/O is needed during evaluation.

    Args:
        symbols: Set of ticker symbol strings.

    Returns:
        Dict mapping symbol -> DataFrame with OHLCV data.

    """
    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore

    store = MarketDataStore()
    data: dict[str, pd.DataFrame] = {}
    failed: list[str] = []
    start = time.time()

    print(f"\n  {DIM}Pre-loading {len(symbols)} symbols from S3 ...{RESET}")

    for sym in sorted(symbols):
        try:
            df = store.read_symbol_data(sym, use_cache=True)
            if df is not None and not df.empty:
                data[sym] = df
            else:
                failed.append(sym)
        except Exception as exc:
            failed.append(sym)
            print(
                f"  {YELLOW}Error loading symbol {sym}: "
                f"{type(exc).__name__}: {exc}{RESET}"
            )

    elapsed = time.time() - start
    print(f"  {GREEN}Loaded {len(data)}/{len(symbols)} symbols "
          f"into memory ({elapsed:.1f}s){RESET}")
    if failed:
        print(f"  {YELLOW}Failed to load: {', '.join(failed)}{RESET}")

    return data


# ---------------------------------------------------------------------------
# Market data adapter for historical backfill (LEGACY - kept for reference)
# ---------------------------------------------------------------------------
def _build_market_data_adapter() -> Any:
    """Build a market data adapter that returns ALL historical data.

    For backfill evaluation, we need ALL data (not filtered from now-period)
    so that the indicator_service.as_of_date truncation can work correctly.
    The standard CachedMarketDataAdapter filters from datetime.now() which
    breaks historical point-in-time evaluation.
    """
    from the_alchemiser.shared.data_v2.cached_market_data_adapter import (
        CachedMarketDataAdapter,
    )
    from the_alchemiser.shared.types.market_data import BarModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol

    class _MaxPeriodAdapter(MarketDataPort):
        """Wrapper that always requests MAX period to get all historical data."""

        def __init__(self) -> None:
            self._inner = CachedMarketDataAdapter()

        def get_bars(
            self,
            symbol: Symbol,
            period: str,  # noqa: ARG002 - we ignore and use MAX
            timeframe: str,
        ) -> list[BarModel]:
            # Always use MAX to get all available data.
            # The indicator_service.as_of_date will truncate to the eval date.
            return self._inner.get_bars(symbol, "MAX", timeframe)

        def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
            return self._inner.get_latest_bar(symbol)

        def get_quote(self, symbol: Symbol) -> Any:
            return self._inner.get_latest_quote(symbol)

    return _MaxPeriodAdapter()


# ---------------------------------------------------------------------------
# Historical-cutoff adapter for point-in-time evaluation
# ---------------------------------------------------------------------------
def _build_historical_adapter(cutoff: date) -> Any:
    """Build a MarketDataPort that filters bars to a cutoff date."""
    import pandas as pd

    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.types.market_data import BarModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol

    class _HistoricalAdapter(MarketDataPort):
        """MarketDataPort filtering bars to a cutoff date."""

        def __init__(self, cutoff_date: date) -> None:
            self.cutoff = cutoff_date
            self._store = MarketDataStore()
            self._cache: dict[str, pd.DataFrame] = {}

        def _df(self, symbol: str) -> pd.DataFrame:
            if symbol not in self._cache:
                df = self._store.read_symbol_data(symbol)
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
            sym = str(symbol)
            df = self._df(sym)
            if df.empty:
                return []
            cutoff_ts = pd.Timestamp(self.cutoff, tz=timezone.utc)
            if df.index.tz is None:
                df.index = df.index.tz_localize(timezone.utc)
            df = df[df.index.normalize() <= cutoff_ts]
            if df.empty:
                return []
            bars: list[BarModel] = []
            for ts, row in df.iterrows():
                bars.append(
                    BarModel(
                        symbol=sym,
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

        def get_quote(self, symbol: Symbol) -> Any:
            return None

    return _HistoricalAdapter(cutoff)


# ---------------------------------------------------------------------------
# Evaluate a group body for a single date (signal only)
# ---------------------------------------------------------------------------
def _evaluate_group_signal(
    ast_body: list[Any],
    eval_date: date,
    engine: Any,
    correlation_id: str,
) -> dict[str, Decimal]:
    """Evaluate a group body at a point-in-time date and return portfolio weights.

    Sets the engine's as_of_date to eval_date, evaluates the AST body,
    and extracts the resulting symbol weights (the "signal").

    This function does NOT compute returns -- it only determines what the
    group would hold on eval_date.  Use ``_calculate_position_return`` to
    compute the return of a held position.

    Args:
        ast_body: AST expressions forming the group body.
        eval_date: The date to evaluate at.
        engine: DSL engine instance.
        correlation_id: Correlation ID for tracing.

    Returns:
        Dictionary of {symbol: weight} for the group's signal on eval_date.
        Empty dict if evaluation produces no weights.

    """
    from engines.dsl.operators.portfolio import (
        PortfolioFragment,
        collect_weights_from_value,
    )
    from the_alchemiser.shared.schemas.trace import Trace

    # Set as-of date so indicators see only data up to eval_date
    engine.indicator_service.as_of_date = eval_date

    # Create a fresh Trace for this evaluation
    trace = Trace(
        trace_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        strategy_id="backfill",
        started_at=datetime.now(UTC),
    )

    last_result = None
    for expr in ast_body:
        last_result = engine.evaluator._evaluate_node(expr, correlation_id, trace)

    # Unwrap single-element list
    if isinstance(last_result, list) and len(last_result) == 1:
        last_result = last_result[0]

    # Extract weights
    if isinstance(last_result, PortfolioFragment):
        return dict(last_result.weights)
    elif isinstance(last_result, dict):
        return {k: Decimal(str(v)) for k, v in last_result.items()}
    elif isinstance(last_result, str):
        return {last_result: Decimal("1")}
    else:
        return collect_weights_from_value(last_result) if last_result else {}


# ---------------------------------------------------------------------------
# Calculate the return of holding a position on a given date
# ---------------------------------------------------------------------------
def _calculate_position_return(
    weights: dict[str, Decimal],
    return_date: date,
    engine: Any,
) -> Decimal | None:
    """Calculate the weighted daily return of a held position on a given date.

    For each symbol in the position, computes the close-to-close return
    on return_date (i.e., close on the preceding trading day to close on
    return_date).  The portfolio return is the weight-normalised sum.

    This answers: "if I was holding these weights going into return_date,
    what return did I earn on return_date?"

    Args:
        weights: Symbol-to-weight mapping representing the held position.
        return_date: The date to compute the return for.
        engine: DSL engine instance (must have indicator_service with
            market_data_service).

    Returns:
        Weighted daily return as Decimal, or None if insufficient data.

    """
    from the_alchemiser.shared.value_objects.symbol import Symbol

    mds = getattr(engine.indicator_service, "market_data_service", None)
    if not mds:
        return None

    weighted_return = Decimal("0")
    total_weight = Decimal("0")
    return_date_str = return_date.isoformat()

    for symbol_str, weight in weights.items():
        if weight <= Decimal("0"):
            continue
        try:
            today = datetime.now(UTC).date()
            days_back = max((today - return_date).days + 5, 30)
            period = f"{days_back}D"
            bars = mds.get_bars(
                symbol=Symbol(symbol_str),
                period=period,
                timeframe="1Day",
            )
            if len(bars) < 2:
                continue

            # Find the bar on or before return_date and its predecessor
            date_to_idx: dict[str, int] = {}
            for i, bar in enumerate(bars):
                date_to_idx[bar.timestamp.date().isoformat()] = i

            target_idx = date_to_idx.get(return_date_str)
            if target_idx is None:
                for i in range(len(bars) - 1, -1, -1):
                    if bars[i].timestamp.date().isoformat() <= return_date_str:
                        target_idx = i
                        break

            if target_idx is None or target_idx < 1:
                continue

            prev_close = bars[target_idx - 1].close
            curr_close = bars[target_idx].close
            if prev_close and prev_close > 0:
                ret = (curr_close - prev_close) / prev_close
                weighted_return += weight * ret
                total_weight += weight
        except (KeyError, IndexError, ValueError, ZeroDivisionError):
            # Symbol has no data or incompatible data for this date.
            # Expected when backfilling with symbols that have different
            # data availability (e.g. FNGU started later than SPY).
            pass
        except Exception as exc:
            print(
                f"  {YELLOW}Unexpected error computing return for "
                f"{symbol_str} on {return_date}: "
                f"{type(exc).__name__}: {exc}{RESET}"
            )

    if total_weight <= Decimal("0"):
        return None

    return weighted_return / total_weight


# ---------------------------------------------------------------------------
# Trading days helper
# ---------------------------------------------------------------------------
def _get_trading_days(end_date: date, num_calendar_days: int) -> list[date]:
    """Generate weekdays (oldest-first) in a calendar date range."""
    start = end_date - timedelta(days=num_calendar_days)
    days: list[date] = []
    current = start
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def _get_trading_days_from_range(start_date: date, end_date: date) -> list[date]:
    """Generate weekdays (oldest-first) from a date range."""
    days: list[date] = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def _discover_available_date_range(
    symbols: set[str],
    *,
    verbose: bool = True,
    preloaded_data: dict[str, pd.DataFrame] | None = None,
) -> tuple[date | None, date | None, dict[str, tuple[date, date]]]:
    """Discover the date range with available market data for the given symbols.

    Returns the date range where ALL symbols have data (most restrictive).

    Args:
        symbols: Set of symbol strings to check.
        verbose: If True, print symbol ranges.
        preloaded_data: Optional pre-loaded DataFrames (avoids S3 reads).

    Returns:
        (start_date, end_date, symbol_ranges) tuple.

    """
    latest_earliest: date | None = None
    earliest_latest: date | None = None
    symbol_ranges: dict[str, tuple[date, date]] = {}

    fallback_store: Any = None
    for symbol in symbols:
        try:
            if preloaded_data and symbol in preloaded_data:
                df = preloaded_data[symbol]
            else:
                if fallback_store is None:
                    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
                    fallback_store = MarketDataStore()
                df = fallback_store.read_symbol_data(symbol)

            if df is None or df.empty:
                continue

            if "timestamp" in df.columns:
                ts_col = pd.to_datetime(df["timestamp"])
            elif df.index.name == "timestamp" or isinstance(df.index, pd.DatetimeIndex):
                ts_col = pd.to_datetime(df.index)
            else:
                continue

            sym_earliest = ts_col.min().date()
            sym_latest = ts_col.max().date()
            symbol_ranges[symbol] = (sym_earliest, sym_latest)

            if latest_earliest is None or sym_earliest > latest_earliest:
                latest_earliest = sym_earliest
            if earliest_latest is None or sym_latest < earliest_latest:
                earliest_latest = sym_latest

        except Exception as exc:
            if verbose:
                print(f"  {YELLOW}WARNING: Could not read data for {symbol}: {exc}{RESET}")

    if verbose and symbol_ranges:
        print(f"\n  {DIM}Symbol data ranges:{RESET}")
        for sym, (s_early, s_late) in sorted(symbol_ranges.items()):
            days_available = len(_get_trading_days_from_range(s_early, s_late))
            is_limiting = (s_early == latest_earliest) or (s_late == earliest_latest)
            marker = f" {YELLOW}<-- limiting{RESET}" if is_limiting else ""
            print(f"    {sym:<10s}  {s_early} to {s_late}  ({days_available} trading days){marker}")

    return latest_earliest, earliest_latest, symbol_ranges


def _discover_single_group_symbols(gi: GroupInfo, engine: Any) -> set[str]:
    """Discover all unique symbols referenced by a single group."""
    return _extract_symbols_from_ast(gi.body)


def _discover_group_symbols(groups: list[GroupInfo], engine: Any) -> set[str]:
    """Discover all unique symbols referenced by a list of groups."""
    symbols: set[str] = set()
    for gi in groups:
        symbols.update(_extract_symbols_from_ast(gi.body))
    return symbols


# Indicator DSL names whose first string argument is a ticker symbol.
_INDICATOR_FUNCTIONS: frozenset[str] = frozenset({
    "rsi", "current-price", "moving-average-price", "moving-average-return",
    "cumulative-return", "exponential-moving-average-price",
    "stdev-return", "stdev-price", "max-drawdown",
    "percentage-price-oscillator", "percentage-price-oscillator-signal",
    "ma", "volatility",
})


def _extract_symbols_from_ast(nodes: list[Any]) -> set[str]:
    """Extract ticker symbols from AST nodes by walking for ``(asset ...)`` forms
    and indicator calls like ``(cumulative-return "FXI" ...)``.

    This is a pure AST walk -- no engine evaluation or indicator computation
    needed.

    Args:
        nodes: List of ASTNode objects to walk.

    Returns:
        Set of ticker symbol strings.

    """
    from the_alchemiser.shared.schemas.ast_node import ASTNode

    symbols: set[str] = set()

    def _is_ticker(value: Any) -> bool:
        """Check if a value looks like a ticker symbol (1-5 uppercase letters)."""
        return isinstance(value, str) and 1 <= len(value) <= 5 and value.isalpha() and value.isupper()

    def _walk(node: Any) -> None:
        if not isinstance(node, ASTNode):
            return

        if node.is_list() and node.children:
            first = node.children[0]
            if first.is_symbol():
                func_name = first.get_symbol_name()

                # Match (asset "TICKER" "description")
                if func_name == "asset" and len(node.children) >= 2:
                    ticker_node = node.children[1]
                    ticker = ticker_node.get_atom_value()
                    if _is_ticker(ticker):
                        symbols.add(ticker)

                # Match (indicator-fn "TICKER" ...)
                elif func_name in _INDICATOR_FUNCTIONS and len(node.children) >= 2:
                    ticker_node = node.children[1]
                    ticker = ticker_node.get_atom_value()
                    if _is_ticker(ticker):
                        symbols.add(ticker)

            # Recurse into all children
            for child in node.children:
                _walk(child)

        elif node.is_list():
            for child in node.children:
                _walk(child)

    for node in nodes:
        _walk(node)

    return symbols


# ---------------------------------------------------------------------------
# Wipe group cache table
# ---------------------------------------------------------------------------
def _wipe_group_cache() -> int:
    """Delete all items from the group history DynamoDB table.

    Scans the table in pages (handling the 1MB scan limit) and
    batch-deletes all items.  Returns the total number of items deleted.
    """
    from engines.dsl.operators.group_cache_lookup import get_dynamodb_table

    table = get_dynamodb_table()
    if table is None:
        print(f"  {RED}Cannot connect to DynamoDB table{RESET}")
        return 0

    total_deleted = 0
    scan_kwargs: dict[str, Any] = {
        "ProjectionExpression": "group_id, record_date",
    }

    while True:
        resp = table.scan(**scan_kwargs)  # type: ignore[attr-defined]
        items = resp.get("Items", [])
        if not items:
            break

        with table.batch_writer() as batch:  # type: ignore[attr-defined]
            for item in items:
                batch.delete_item(
                    Key={
                        "group_id": item["group_id"],
                        "record_date": item["record_date"],
                    }
                )

        total_deleted += len(items)
        print(f"  {DIM}Deleted {len(items)} items ({total_deleted} total)...{RESET}")

        if "LastEvaluatedKey" not in resp:
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    return total_deleted


# ---------------------------------------------------------------------------
# Batch DynamoDB writer
# ---------------------------------------------------------------------------
def _batch_write_dynamodb(
    items: list[dict[str, Any]],
    *,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Batch-write cache entries to DynamoDB. Returns (written, failed).

    Uses the DynamoDB batch_writer context manager which automatically
    handles batching (max 25 items per BatchWriteItem request) and
    unprocessed item retries.

    Args:
        items: List of dicts with keys: group_id, record_date, selections,
            portfolio_daily_return.
        dry_run: If True, skip writing.

    Returns:
        Tuple of (items_written, items_failed).

    """
    if dry_run or not items:
        return (len(items) if dry_run else 0), 0

    from engines.dsl.operators.group_cache_lookup import get_dynamodb_table

    table = get_dynamodb_table()
    if table is None:
        return 0, len(items)

    ttl_epoch = int((datetime.now(UTC) + timedelta(days=30)).timestamp())
    written = 0
    failed = 0

    try:
        with table.batch_writer() as batch:  # type: ignore[attr-defined]
            for item in items:
                try:
                    batch.put_item(
                        Item={
                            "group_id": item["group_id"],
                            "record_date": item["record_date"],
                            "selections": item["selections"],
                            "selection_count": len(item["selections"]),
                            "portfolio_daily_return": str(
                                item["portfolio_daily_return"]
                            ),
                            "evaluated_at": datetime.now(UTC).isoformat(),
                            "source": "on_demand_backfill",
                            "ttl": ttl_epoch,
                        }
                    )
                    written += 1
                except Exception as exc:
                    failed += 1
                    print(
                        f"  {YELLOW}DynamoDB put_item failed for "
                        f"group_id={item.get('group_id')}, "
                        f"record_date={item.get('record_date')}: "
                        f"{type(exc).__name__}: {exc}{RESET}"
                    )
    except Exception as exc:
        # Entire batch operation failed
        print(
            f"  {RED}DynamoDB batch_writer failed: "
            f"{type(exc).__name__}: {exc}{RESET}"
        )
        return written, len(items) - written

    return written, failed


# ---------------------------------------------------------------------------
# Single-group backfill (used by both sequential and parallel paths)
# ---------------------------------------------------------------------------
def _backfill_single_group(
    gi: GroupInfo,
    group_id: str,
    trading_days: list[date],
    engine: Any,
    correlation_id: str,
    *,
    quiet: bool = False,
) -> dict[str, Any]:
    """Run the position-tracking backfill loop for one group.

    Returns a result dict containing the list of DynamoDB items to write
    and summary statistics.  Does NOT write to DynamoDB -- the caller
    handles batching.

    Args:
        gi: GroupInfo with AST body.
        group_id: Deterministic cache key.
        trading_days: Ordered list of dates to evaluate.
        engine: DslEngine instance.
        correlation_id: Tracing identifier.
        quiet: If True, suppress per-day output (for parallel workers).

    Returns:
        Dict with keys: group_name, group_id, items, days_evaluated,
        days_written, days_skipped, days_failed, elapsed_seconds.

    """
    ast_body = gi.body
    group_name = gi.name
    dynamo_items: list[dict[str, Any]] = []
    skipped = 0
    failed = 0
    group_start = time.time()

    prev_weights: dict[str, Decimal] | None = None

    for day_idx, eval_date in enumerate(trading_days):
        progress = f"  [{day_idx + 1}/{len(trading_days)}] {eval_date}"
        try:
            today_weights = _evaluate_group_signal(
                ast_body, eval_date, engine, correlation_id,
            )

            if prev_weights is None:
                if not today_weights:
                    if not quiet:
                        print(f"{progress}  {DIM}-- no signal{RESET}")
                    skipped += 1
                    continue
                if not quiet:
                    symbols = ", ".join(sorted(today_weights.keys()))
                    print(f"{progress}  {DIM}-- first signal [{symbols}], "
                          f"no return yet{RESET}")
                prev_weights = today_weights
                continue

            daily_ret = _calculate_position_return(
                prev_weights, eval_date, engine,
            )

            if daily_ret is None:
                if not quiet:
                    print(f"{progress}  {DIM}-- no price data{RESET}")
                skipped += 1
                if today_weights:
                    prev_weights = today_weights
                continue

            held_selections_str = {
                sym: str(w) for sym, w in prev_weights.items()
            }
            dynamo_items.append({
                "group_id": group_id,
                "record_date": eval_date.isoformat(),
                "selections": held_selections_str,
                "portfolio_daily_return": daily_ret,
            })

            if not quiet:
                held_symbols = ", ".join(sorted(prev_weights.keys()))
                ret_pct = float(daily_ret) * 100
                signal_change = ""
                if (
                    today_weights
                    and set(today_weights.keys()) != set(prev_weights.keys())
                ):
                    new_syms = ", ".join(sorted(today_weights.keys()))
                    signal_change = f"  -> [{new_syms}]"
                print(
                    f"{progress}  ret={ret_pct:+.4f}%  "
                    f"held=[{held_symbols}]{signal_change}"
                )

            if today_weights:
                prev_weights = today_weights

        except Exception as exc:
            if not quiet:
                print(f"{progress}  {RED}ERROR: {exc}{RESET}")
            failed += 1

    elapsed = time.time() - group_start
    return {
        "group_name": group_name,
        "group_id": group_id,
        "items": dynamo_items,
        "days_evaluated": len(trading_days),
        "days_written": len(dynamo_items),
        "days_skipped": skipped,
        "days_failed": failed,
        "elapsed_seconds": round(elapsed, 1),
    }


# ---------------------------------------------------------------------------
# Parallel worker (runs in forked subprocess)
# ---------------------------------------------------------------------------
def _parallel_worker(group_name: str) -> dict[str, Any]:
    """Worker function for ProcessPoolExecutor (fork mode).

    Reads shared state from module-level ``_WORKER_STATE`` (inherited
    via fork).  Builds its own DslEngine to avoid shared mutable state.

    Args:
        group_name: Name of the group to backfill.

    Returns:
        Result dict from ``_backfill_single_group``.

    """
    import logging as _logging
    import structlog as _structlog

    # Suppress logging in worker
    _structlog.configure(
        wrapper_class=_structlog.make_filtering_bound_logger(_logging.ERROR)
    )
    for name in [
        "strategy_v2", "the_alchemiser", "engines",
        "indicators", "botocore", "urllib3",
    ]:
        _logging.getLogger(name).setLevel(_logging.ERROR)

    state = _WORKER_STATE
    gi: GroupInfo = state["groups_by_name"][group_name]
    trading_days: list[date] = state["trading_days_by_group"][group_name]
    preloaded_data: dict[str, pd.DataFrame] = state["preloaded_data"]
    strategies_dir: Path = state["strategies_dir"]
    clj_filename: str = state["clj_filename"]
    correlation_id: str = state["correlation_id"]

    from engines.dsl.engine import DslEngine
    from engines.dsl.operators.group_scoring import clear_evaluation_caches
    from engines.dsl.operators.portfolio import _derive_group_id

    # Each worker gets its own engine with in-memory adapter
    adapter = _InMemoryAdapter(preloaded_data)
    engine = DslEngine(
        strategy_config_path=strategies_dir,
        market_data_adapter=adapter,
        debug_mode=False,
    )

    clear_evaluation_caches()
    try:
        engine.evaluate_strategy(clj_filename, correlation_id)
    except Exception:
        # Warm-up may fail if some symbols lack data; per-day eval
        # will handle missing data gracefully per group.
        pass

    group_id = _derive_group_id(group_name)
    return _backfill_single_group(
        gi, group_id, trading_days, engine, correlation_id, quiet=True,
    )


# ---------------------------------------------------------------------------
# Main backfill logic
# ---------------------------------------------------------------------------
def backfill_strategy_groups(
    clj_path: str,
    *,
    lookback_days: int | None = 45,
    backfill_all: bool = False,
    warmup_days: int = INDICATOR_WARMUP_DAYS,
    dry_run: bool = False,
    wipe: bool = False,
    group_patterns: list[str] | None = None,
    parallel_workers: int = 1,
    target_level: int | None = None,
) -> dict[str, Any]:
    """Backfill DynamoDB group cache for all groups in a .clj strategy file.

    Processes groups in depth-level passes (deepest first) so that inner
    groups complete before outer groups that may depend on them.  Within
    each depth level, groups can be processed in parallel.

    Args:
        clj_path: Path to .clj strategy file (absolute or relative).
        lookback_days: Calendar days to backfill. Ignored if backfill_all=True.
        backfill_all: If True, backfill all available historical data.
        warmup_days: Trading days for indicator warm-up period.
        dry_run: If True, compute but do not write to DynamoDB.
        wipe: If True, delete all existing cache entries before backfilling.
        group_patterns: Optional list of glob patterns to filter groups.
        parallel_workers: Number of parallel workers (1 = sequential).
        target_level: If set, only process groups at this depth level.

    Returns:
        Summary dict with per-group results.

    """
    import logging as _logging
    import structlog as _structlog

    # Suppress noisy logs during evaluation
    _structlog.configure(
        wrapper_class=_structlog.make_filtering_bound_logger(_logging.WARNING)
    )
    _logging.getLogger("strategy_v2").setLevel(_logging.WARNING)
    _logging.getLogger("the_alchemiser").setLevel(_logging.WARNING)
    _logging.getLogger("engines").setLevel(_logging.WARNING)
    _logging.getLogger("indicators").setLevel(_logging.WARNING)
    _logging.getLogger("botocore").setLevel(_logging.WARNING)
    _logging.getLogger("urllib3").setLevel(_logging.WARNING)

    from engines.dsl.engine import DslEngine
    from engines.dsl.operators.group_scoring import clear_evaluation_caches
    from engines.dsl.operators.portfolio import _derive_group_id
    from engines.dsl.sexpr_parser import SexprParser

    # Resolve the .clj file path
    clj_file = Path(clj_path)
    if not clj_file.exists():
        clj_file = STRATEGIES_DIR / clj_path
    if not clj_file.exists():
        clj_file = STRATEGIES_DIR / Path(clj_path).name
    if not clj_file.exists():
        print(f"{RED}ERROR: Cannot find strategy file: {clj_path}{RESET}")
        sys.exit(1)

    strategy_name = clj_file.stem

    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  Group Cache Backfill: {strategy_name}{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print(f"  File:     {clj_file}")
    if backfill_all:
        print(f"  Mode:     ALL available history")
    else:
        print(f"  Lookback: {lookback_days} calendar days")
    print(f"  Dry run:  {dry_run}")
    print(f"  Wipe:     {wipe}")
    print(f"  Workers:  {parallel_workers}")
    if target_level is not None:
        print(f"  Level:    {target_level} only")
    print(f"  Table:    {os.environ.get('GROUP_HISTORY_TABLE', '(not set)')}")

    # ---- Wipe existing cache if requested ----
    if wipe and not dry_run:
        table_name = os.environ.get("GROUP_HISTORY_TABLE", "(not set)")
        print(f"\n{BOLD}  Wiping group cache table: {table_name}{RESET}")
        deleted = _wipe_group_cache()
        if deleted > 0:
            print(f"  {GREEN}Wiped {deleted} items from {table_name}{RESET}")
        else:
            print(f"  {DIM}Table was already empty{RESET}")
    elif wipe and dry_run:
        print(f"\n  {YELLOW}DRY RUN -- skipping wipe{RESET}")

    # ---- Parse the strategy file ----
    print(f"\n{DIM}Parsing strategy file ...{RESET}", end="", flush=True)
    parser = SexprParser()
    ast = parser.parse_file(str(clj_file))
    print(f" done.{RESET}")

    # ---- Discover filter-targeted groups ----
    all_filter_groups = _find_filter_targeted_groups(ast)

    # Deduplicate by name, keeping the deepest occurrence
    best_by_name: dict[str, GroupInfo] = {}
    for gi in all_filter_groups:
        existing = best_by_name.get(gi.name)
        if existing is None or gi.depth > existing.depth:
            best_by_name[gi.name] = gi

    unique_groups_sorted: list[GroupInfo] = sorted(
        best_by_name.values(),
        key=lambda g: (-g.depth, g.name),
    )

    # Apply group pattern filter
    if group_patterns:
        unique_groups_sorted = [
            gi for gi in unique_groups_sorted
            if any(fnmatch(gi.name, pat) for pat in group_patterns)
        ]

    # ---- Group by depth level ----
    depth_groups: dict[int, list[GroupInfo]] = defaultdict(list)
    for gi in unique_groups_sorted:
        depth_groups[gi.depth].append(gi)

    # Filter to target level if specified
    if target_level is not None:
        if target_level not in depth_groups:
            available = sorted(depth_groups.keys(), reverse=True)
            print(f"\n{YELLOW}No groups at depth {target_level}. "
                  f"Available depths: {available}{RESET}")
            return {"groups": {}, "total_writes": 0}
        depth_groups = {target_level: depth_groups[target_level]}

    # Show discovery summary
    total_groups = sum(len(gs) for gs in depth_groups.values())
    print(f"\n  Found {len(all_filter_groups)} filter-targeted group nodes, "
          f"{total_groups} unique groups across {len(depth_groups)} depth levels")

    if total_groups == 0:
        print(f"\n{YELLOW}No filter-targeted groups found to backfill.{RESET}")
        return {"groups": {}, "total_writes": 0}

    for depth in sorted(depth_groups.keys(), reverse=True):
        groups = depth_groups[depth]
        print(f"\n  {BOLD}Depth {depth} ({len(groups)} groups):{RESET}")
        for i, gi in enumerate(groups, 1):
            gid = _derive_group_id(gi.name)
            print(f"    {i:3d}. {gi.name[:48]:<48s}  "
                  f"{DIM}{gid}  (metric: {gi.parent_filter_metric}){RESET}")

    # ---- Discover ALL symbols across ALL groups (pure AST walk, no engine) ----
    print(f"\n{DIM}Discovering symbols across all groups (AST scan) ...{RESET}")
    all_symbols: set[str] = set()
    symbols_by_group: dict[str, set[str]] = {}
    for gi in unique_groups_sorted:
        group_syms = _extract_symbols_from_ast(gi.body)
        symbols_by_group[gi.name] = group_syms
        all_symbols.update(group_syms)
        if group_syms:
            print(f"  {DIM}{gi.name[:40]}: {', '.join(sorted(group_syms))}{RESET}")
    print(f"  Total unique symbols: {len(all_symbols)}")

    # ---- Pre-load ALL market data into memory ----
    preloaded_data = _preload_all_market_data(all_symbols)

    correlation_id = f"backfill-{strategy_name}-{datetime.now(UTC).strftime('%H%M%S')}"

    # ---- Determine trading days ----
    end_date = datetime.now(UTC).date()

    # ---- Process each depth level (deepest first) ----
    results: dict[str, dict[str, Any]] = {}
    total_writes = 0
    total_failures = 0
    overall_start = time.time()

    for depth in sorted(depth_groups.keys(), reverse=True):
        level_groups = depth_groups[depth]

        print(f"\n{BOLD}{'=' * 72}{RESET}")
        print(f"{BOLD}  DEPTH LEVEL {depth} -- "
              f"{len(level_groups)} group(s){RESET}")
        print(f"{BOLD}{'=' * 72}{RESET}")

        # Pre-compute trading days for each group at this level
        trading_days_by_group: dict[str, list[date]] = {}
        for gi in level_groups:
            group_id = _derive_group_id(gi.name)

            if backfill_all:
                group_symbols = symbols_by_group.get(gi.name, set())
                if not group_symbols:
                    print(f"  {YELLOW}WARNING: No symbols for {gi.name}, skipping{RESET}")
                    results[gi.name] = {
                        "group_id": group_id,
                        "days_evaluated": 0, "days_written": 0,
                        "days_skipped": 0, "days_failed": 0,
                        "elapsed_seconds": 0, "records": [],
                    }
                    continue

                start_date, data_end_date, _ = _discover_available_date_range(
                    group_symbols, verbose=False, preloaded_data=preloaded_data,
                )
                if start_date is None or data_end_date is None:
                    print(f"  {YELLOW}WARNING: No data for {gi.name}, skipping{RESET}")
                    results[gi.name] = {
                        "group_id": group_id,
                        "days_evaluated": 0, "days_written": 0,
                        "days_skipped": 0, "days_failed": 0,
                        "elapsed_seconds": 0, "records": [],
                    }
                    continue

                warmup_calendar_days = int(warmup_days * 7 / 5) + 5
                eval_start = start_date + timedelta(days=warmup_calendar_days)
                if eval_start >= end_date:
                    print(f"  {YELLOW}WARNING: Not enough warm-up data for "
                          f"{gi.name}, skipping{RESET}")
                    results[gi.name] = {
                        "group_id": group_id,
                        "days_evaluated": 0, "days_written": 0,
                        "days_skipped": 0, "days_failed": 0,
                        "elapsed_seconds": 0, "records": [],
                    }
                    continue

                trading_days_by_group[gi.name] = _get_trading_days_from_range(
                    eval_start, end_date,
                )
                print(f"  {gi.name[:45]}: {len(trading_days_by_group[gi.name])} "
                      f"trading days ({eval_start} to {end_date})")
            else:
                effective_lookback = lookback_days or 45
                trading_days_by_group[gi.name] = _get_trading_days(
                    end_date, effective_lookback,
                )

        # Filter to groups that have trading days
        processable = [
            gi for gi in level_groups if gi.name in trading_days_by_group
        ]
        if not processable:
            print(f"  {YELLOW}No processable groups at depth {depth}{RESET}")
            continue

        # ---- Process groups at this level ----
        level_items: list[dict[str, Any]] = []
        level_start = time.time()

        if parallel_workers > 1 and len(processable) > 1:
            # ---- PARALLEL MODE ----
            print(f"\n  {CYAN}Processing {len(processable)} groups in parallel "
                  f"({parallel_workers} workers) ...{RESET}")

            # Set up shared state for workers (inherited via fork)
            global _WORKER_STATE
            _WORKER_STATE = {
                "groups_by_name": {gi.name: gi for gi in processable},
                "trading_days_by_group": trading_days_by_group,
                "preloaded_data": preloaded_data,
                "strategies_dir": STRATEGIES_DIR,
                "clj_filename": clj_file.name,
                "correlation_id": correlation_id,
            }

            ctx = mp.get_context("fork")
            with ProcessPoolExecutor(
                max_workers=min(parallel_workers, len(processable)),
                mp_context=ctx,
            ) as executor:
                future_to_name = {
                    executor.submit(_parallel_worker, gi.name): gi.name
                    for gi in processable
                }
                for future in as_completed(future_to_name):
                    gname = future_to_name[future]
                    try:
                        result = future.result()
                        level_items.extend(result["items"])
                        results[gname] = result
                        print(f"  {GREEN}Completed: {gname[:45]} "
                              f"({result['days_written']} days, "
                              f"{result['elapsed_seconds']:.1f}s){RESET}")
                    except Exception as exc:
                        print(f"  {RED}FAILED: {gname[:45]} -- {exc}{RESET}")
                        results[gname] = {
                            "group_id": _derive_group_id(gname),
                            "days_evaluated": 0, "days_written": 0,
                            "days_skipped": 0, "days_failed": 1,
                            "elapsed_seconds": 0, "records": [],
                        }
                        total_failures += 1
        else:
            # ---- SEQUENTIAL MODE ----
            # Build one engine for the entire level (reused across groups)
            adapter = _InMemoryAdapter(preloaded_data)
            engine = DslEngine(
                strategy_config_path=STRATEGIES_DIR,
                market_data_adapter=adapter,
                debug_mode=False,
            )
            clear_evaluation_caches()
            try:
                engine.evaluate_strategy(clj_file.name, correlation_id)
            except Exception as warm_exc:
                print(f"  {YELLOW}Warm-up eval failed ({type(warm_exc).__name__}: "
                      f"{warm_exc}); continuing per-group ...{RESET}")

            for gi in processable:
                group_id = _derive_group_id(gi.name)
                trading_days = trading_days_by_group[gi.name]

                print(f"\n  {BOLD}{gi.name} (depth={gi.depth}){RESET}")
                print(f"    group_id: {DIM}{group_id}{RESET}")
                print(f"    days:     {len(trading_days)}")

                result = _backfill_single_group(
                    gi, group_id, trading_days, engine, correlation_id,
                )
                level_items.extend(result["items"])
                results[gi.name] = result

                print(f"    {DIM}Summary: {result['days_written']} computed, "
                      f"{result['days_skipped']} skipped, "
                      f"{result['days_failed']} failed "
                      f"({result['elapsed_seconds']:.1f}s){RESET}")

            # Restore as_of_date
            engine.indicator_service.as_of_date = None

        level_elapsed = time.time() - level_start

        # ---- Batch write all items for this level ----
        if level_items:
            print(f"\n  {DIM}Batch writing {len(level_items)} items to "
                  f"DynamoDB ...{RESET}", end="", flush=True)
            written, failed = _batch_write_dynamodb(
                level_items, dry_run=dry_run,
            )
            total_writes += written
            total_failures += failed
            status = f"{GREEN}OK{RESET}" if failed == 0 else f"{RED}{failed} failed{RESET}"
            if dry_run:
                status = f"{YELLOW}DRY RUN{RESET}"
            print(f" {written} written, {status} ({level_elapsed:.1f}s)")
        else:
            print(f"\n  {DIM}No items to write for depth {depth}{RESET}")

    overall_elapsed = time.time() - overall_start

    # ---- Final report ----
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  BACKFILL REPORT{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print(f"  Strategy:        {strategy_name}")
    print(f"  DynamoDB table:  {os.environ.get('GROUP_HISTORY_TABLE', '(not set)')}")
    lookback_mode = (
        "ALL available history (per-group)" if backfill_all
        else f"{lookback_days or 45} calendar days"
    )
    print(f"  Lookback:        {lookback_mode}")
    print(f"  Write mode:      {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"  Workers:         {parallel_workers}")
    print(f"  Duration:        {overall_elapsed:.1f}s")
    print(f"  Groups:          {len(results)}")
    print(f"  Total writes:    {total_writes}")
    print(f"  Total failures:  {total_failures}")

    print(f"\n  {BOLD}Per-group breakdown:{RESET}")
    print(f"  {'Group':<50s}  {'Days':>5s}  {'Written':>7s}  "
          f"{'Skip':>4s}  {'Fail':>4s}  {'Time':>6s}")
    print(f"  {'-' * 50}  {'-' * 5}  {'-' * 7}  "
          f"{'-' * 4}  {'-' * 4}  {'-' * 6}")
    for gname, gdata in results.items():
        d = gdata["days_evaluated"]
        w = gdata["days_written"]
        s = gdata["days_skipped"]
        f = gdata["days_failed"]
        t = gdata["elapsed_seconds"]
        color = GREEN if f == 0 and w > 0 else (RED if f > 0 else YELLOW)
        print(f"  {gname[:50]:<50s}  {d:>5d}  {color}{w:>7d}{RESET}  "
              f"{s:>4d}  {f:>4d}  {t:>5.1f}s")

    if total_failures > 0:
        print(f"\n  {RED}WARNING: {total_failures} write(s) failed -- "
              f"check IAM permissions and table configuration{RESET}")
    elif total_writes == 0 and not dry_run:
        print(f"\n  {YELLOW}WARNING: Zero records written -- "
              f"all days produced no data{RESET}")
    elif dry_run:
        print(f"\n  {YELLOW}DRY RUN -- no records were written "
              f"to DynamoDB{RESET}")
    else:
        print(f"\n  {GREEN}All records written successfully{RESET}")

    # ---- Verification: re-read from DynamoDB ----
    if not dry_run and total_writes > 0:
        print(f"\n{BOLD}  Verification (re-reading from DynamoDB):{RESET}")
        from engines.dsl.operators.group_cache_lookup import (
            lookup_historical_returns,
        )

        for gname, gdata in results.items():
            gid = gdata["group_id"]
            days_evaluated = gdata["days_evaluated"]
            if days_evaluated == 0:
                continue

            verify_lookback = int(days_evaluated * 1.5) + 10
            returns = lookup_historical_returns(
                group_id=gid,
                lookback_days=verify_lookback,
                end_date=end_date,
            )
            expected = gdata["days_written"]
            actual = len(returns)
            match = GREEN + "MATCH" if actual >= expected else RED + "MISMATCH"
            print(f"    {gname[:45]:<45s}  expected>={expected:>3d}  "
                  f"actual={actual:>3d}  {match}{RESET}")

    print()
    return {"groups": results, "total_writes": total_writes}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill DynamoDB group cache for a .clj strategy file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --days 60
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --all
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --all --warmup 60
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --dry-run
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --group "WYLD*"
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --parallel 4
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --level 2
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --wipe --all --parallel 4
        """,
    )
    parser.add_argument(
        "strategy_file",
        help="Path to .clj strategy file (absolute, relative, or just filename)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Calendar days to backfill (default: 45, ignored if --all is used)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="backfill_all",
        help="Backfill ALL available historical data (as far back as data exists)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=INDICATOR_WARMUP_DAYS,
        help=f"Trading days for indicator warm-up period (default: {INDICATOR_WARMUP_DAYS}). "
             "Indicators like max_drawdown, SMA, RSI need historical data to calculate. "
             "Only used with --all.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute returns but do not write to DynamoDB",
    )
    parser.add_argument(
        "--group",
        action="append",
        dest="groups",
        help="Glob pattern to filter group names (can repeat). "
             "E.g. --group 'WYLD*' --group 'WAM*'",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        metavar="N",
        help="Number of parallel workers for groups at same depth level. "
             "Uses fork-based multiprocessing. Default: 1 (sequential).",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=None,
        metavar="DEPTH",
        help="Process only groups at this depth level. "
             "Run deepest first (e.g. --level 2 then --level 1 then --level 0).",
    )
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="Delete all existing cache entries from DynamoDB before backfilling. "
             "Use with --all for a clean rebuild.",
    )

    args = parser.parse_args()

    lookback_days = args.days if args.days is not None else (
        None if args.backfill_all else 45
    )

    backfill_strategy_groups(
        clj_path=args.strategy_file,
        lookback_days=lookback_days,
        backfill_all=args.backfill_all,
        warmup_days=args.warmup,
        dry_run=args.dry_run,
        wipe=args.wipe,
        group_patterns=args.groups,
        parallel_workers=args.parallel,
        target_level=args.level,
    )


if __name__ == "__main__":
    main()
