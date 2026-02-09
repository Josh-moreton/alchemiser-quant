#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Backfill DynamoDB group cache for all named groups in a .clj strategy file.

Parses the strategy file, discovers all ``(group "Name" ...)`` nodes,
evaluates each group's AST body for every trading day in the lookback
window, computes weighted portfolio daily returns, writes them to the
``GroupHistoricalSelectionsTable`` in DynamoDB, and prints a summary
report of what was uploaded.

Usage:
    poetry run python scripts/backfill_group_cache.py \\
        layers/shared/the_alchemiser/shared/strategies/ftl_starburst.clj

    # Custom lookback (default 45 calendar days):
    poetry run python scripts/backfill_group_cache.py \\
        ftl_starburst.clj --days 60

    # Dry-run (compute but do not write to DynamoDB):
    poetry run python scripts/backfill_group_cache.py \\
        ftl_starburst.clj --dry-run

    # Target specific group(s):
    poetry run python scripts/backfill_group_cache.py \\
        ftl_starburst.clj --group "WYLD Mean Reversion*"
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
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
# Market data adapter for historical backfill
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
# Evaluate a group body for a single date
# ---------------------------------------------------------------------------
def _evaluate_group_for_date(
    ast_body: list[Any],
    eval_date: date,
    engine: Any,
    correlation_id: str,
) -> tuple[dict[str, Decimal], Decimal | None]:
    """Evaluate a group body at a point-in-time date.

    Returns (weights_dict, daily_return_or_None).
    """
    import uuid

    from engines.dsl.operators.portfolio import (
        PortfolioFragment,
        collect_weights_from_value,
    )
    from the_alchemiser.shared.schemas.trace import Trace
    from the_alchemiser.shared.value_objects.symbol import Symbol

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
        day_weights = dict(last_result.weights)
    elif isinstance(last_result, dict):
        day_weights = {k: Decimal(str(v)) for k, v in last_result.items()}
    elif isinstance(last_result, str):
        day_weights = {last_result: Decimal("1")}
    else:
        day_weights = collect_weights_from_value(last_result) if last_result else {}

    if not day_weights:
        return {}, None

    # Compute portfolio daily return
    mds = getattr(engine.indicator_service, "market_data_service", None)
    if not mds:
        return day_weights, None

    weighted_return = Decimal("0")
    total_weight = Decimal("0")
    record_date_str = eval_date.isoformat()

    for symbol_str, weight in day_weights.items():
        if weight <= Decimal("0"):
            continue
        try:
            today = datetime.now(UTC).date()
            days_back = max((today - eval_date).days + 5, 30)
            period = f"{days_back}D"
            bars = mds.get_bars(
                symbol=Symbol(symbol_str),
                period=period,
                timeframe="1Day",
            )
            if len(bars) < 2:
                continue

            # Find the bar on or before record_date and its predecessor
            date_to_idx: dict[str, int] = {}
            for i, bar in enumerate(bars):
                date_to_idx[bar.timestamp.date().isoformat()] = i

            target_idx = date_to_idx.get(record_date_str)
            if target_idx is None:
                for i in range(len(bars) - 1, -1, -1):
                    if bars[i].timestamp.date().isoformat() <= record_date_str:
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
        except Exception as exc:
            print(
                f"{progress}  {YELLOW}WARNING: failed to get bars for "
                f"{symbol_str} on {record_date_str}: {exc}{RESET}"
            )

    if total_weight <= Decimal("0"):
        return day_weights, None

    return day_weights, weighted_return / total_weight


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


# ---------------------------------------------------------------------------
# DynamoDB writer
# ---------------------------------------------------------------------------
def _write_to_dynamodb(
    group_id: str,
    record_date: str,
    selections: dict[str, str],
    portfolio_daily_return: Decimal,
    *,
    dry_run: bool = False,
) -> bool:
    """Write a single cache entry to DynamoDB. Returns True on success."""
    if dry_run:
        return True

    from engines.dsl.operators.group_cache_lookup import write_historical_return

    return write_historical_return(
        group_id=group_id,
        record_date=record_date,
        selections=selections,
        portfolio_daily_return=portfolio_daily_return,
    )


# ---------------------------------------------------------------------------
# Main backfill logic
# ---------------------------------------------------------------------------
def backfill_strategy_groups(
    clj_path: str,
    *,
    lookback_days: int = 45,
    dry_run: bool = False,
    group_patterns: list[str] | None = None,
) -> dict[str, Any]:
    """Backfill DynamoDB group cache for all groups in a .clj strategy file.

    Args:
        clj_path: Path to .clj strategy file (absolute or relative).
        lookback_days: Calendar days to backfill.
        dry_run: If True, compute but do not write to DynamoDB.
        group_patterns: Optional list of glob patterns to filter groups.

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
        # Try relative to strategies dir
        clj_file = STRATEGIES_DIR / clj_path
    if not clj_file.exists():
        # Try just the filename
        clj_file = STRATEGIES_DIR / Path(clj_path).name
    if not clj_file.exists():
        print(f"{RED}ERROR: Cannot find strategy file: {clj_path}{RESET}")
        sys.exit(1)

    strategy_name = clj_file.stem

    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  Group Cache Backfill: {strategy_name}{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print(f"  File:     {clj_file}")
    print(f"  Lookback: {lookback_days} calendar days")
    print(f"  Dry run:  {dry_run}")
    print(f"  Table:    {os.environ.get('GROUP_HISTORY_TABLE', '(not set)')}")

    # ---- Parse the strategy file ----
    print(f"\n{DIM}Parsing strategy file ...{RESET}", end="", flush=True)
    parser = SexprParser()
    ast = parser.parse_file(str(clj_file))
    print(f" done.{RESET}")

    # ---- Discover filter-targeted groups (only these need cache) ----
    all_filter_groups = _find_filter_targeted_groups(ast)

    # Deduplicate by name, keeping the deepest occurrence
    best_by_name: dict[str, GroupInfo] = {}
    for gi in all_filter_groups:
        existing = best_by_name.get(gi.name)
        if existing is None or gi.depth > existing.depth:
            best_by_name[gi.name] = gi

    # Sort deepest-first (bottom-up) so inner groups are backfilled before
    # outer groups that depend on them
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

    print(f"\n  Found {len(all_filter_groups)} filter-targeted group nodes, "
          f"{len(unique_groups_sorted)} unique groups to backfill (bottom-up)")

    if not unique_groups_sorted:
        print(f"\n{YELLOW}No filter-targeted groups found to backfill.{RESET}")
        return {"groups": {}, "total_writes": 0}

    for i, gi in enumerate(unique_groups_sorted, 1):
        gid = _derive_group_id(gi.name)
        print(f"    {i:3d}. [depth={gi.depth}] {gi.name[:48]:<48s}  "
              f"{DIM}{gid}  (metric: {gi.parent_filter_metric}){RESET}")

    # ---- Build engine ----
    print(f"\n{DIM}Initializing market data ...{RESET}", end="", flush=True)
    adapter = _build_market_data_adapter()
    engine = DslEngine(
        strategy_config_path=STRATEGIES_DIR,
        market_data_adapter=adapter,
        debug_mode=False,
    )
    print(f" done.{RESET}")

    # ---- First, run a full evaluation so AST bodies get registered ----
    print(f"{DIM}Running initial strategy evaluation to register AST bodies ...{RESET}",
          end="", flush=True)
    clear_evaluation_caches()
    correlation_id = f"backfill-{strategy_name}-{datetime.now(UTC).strftime('%H%M%S')}"
    engine.evaluate_strategy(clj_file.name, correlation_id)
    print(f" done.{RESET}")

    # ---- Determine trading days ----
    end_date = datetime.now(UTC).date()
    trading_days = _get_trading_days(end_date, lookback_days)
    print(f"\n  Trading days in window: {len(trading_days)} "
          f"({trading_days[0]} to {trading_days[-1]})")

    # ---- Backfill each group ----
    results: dict[str, dict[str, Any]] = {}
    total_writes = 0
    total_failures = 0
    overall_start = time.time()

    for group_idx, gi in enumerate(unique_groups_sorted, 1):
        group_name = gi.name
        ast_body = gi.body
        group_id = _derive_group_id(group_name)
        print(f"\n{BOLD}[{group_idx}/{len(unique_groups_sorted)}] "
              f"{group_name} (depth={gi.depth}){RESET}")
        print(f"  group_id: {DIM}{group_id}{RESET}")
        print(f"  metric:   {DIM}{gi.parent_filter_metric}{RESET}")

        group_results: list[dict[str, Any]] = []
        wrote = 0
        skipped = 0
        failed = 0
        group_start = time.time()

        for day_idx, eval_date in enumerate(trading_days):
            progress = f"  [{day_idx + 1}/{len(trading_days)}] {eval_date}"
            try:
                weights, daily_ret = _evaluate_group_for_date(
                    ast_body, eval_date, engine, correlation_id,
                )

                if not weights or daily_ret is None:
                    print(f"{progress}  {DIM}-- no data{RESET}")
                    skipped += 1
                    continue

                selections_str = {sym: str(w) for sym, w in weights.items()}
                ok = _write_to_dynamodb(
                    group_id=group_id,
                    record_date=eval_date.isoformat(),
                    selections=selections_str,
                    portfolio_daily_return=daily_ret,
                    dry_run=dry_run,
                )

                symbols = ", ".join(sorted(weights.keys()))
                ret_pct = float(daily_ret) * 100
                status = f"{GREEN}OK{RESET}" if ok else f"{RED}FAIL{RESET}"
                if dry_run:
                    status = f"{YELLOW}DRY{RESET}"

                print(f"{progress}  ret={ret_pct:+.4f}%  [{symbols}]  {status}")

                group_results.append({
                    "date": eval_date.isoformat(),
                    "selections": selections_str,
                    "daily_return": str(daily_ret),
                    "written": ok,
                })

                if ok:
                    wrote += 1
                else:
                    failed += 1

            except Exception as exc:
                print(f"{progress}  {RED}ERROR: {exc}{RESET}")
                failed += 1

        elapsed = time.time() - group_start
        results[group_name] = {
            "group_id": group_id,
            "days_evaluated": len(trading_days),
            "days_written": wrote,
            "days_skipped": skipped,
            "days_failed": failed,
            "elapsed_seconds": round(elapsed, 1),
            "records": group_results,
        }
        total_writes += wrote
        total_failures += failed

        print(f"  {DIM}Summary: {wrote} written, {skipped} skipped, "
              f"{failed} failed ({elapsed:.1f}s){RESET}")

    # Restore as_of_date
    engine.indicator_service.as_of_date = None

    overall_elapsed = time.time() - overall_start

    # ---- Final report ----
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  BACKFILL REPORT{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print(f"  Strategy:        {strategy_name}")
    print(f"  DynamoDB table:  {os.environ.get('GROUP_HISTORY_TABLE', '(not set)')}")
    print(f"  Mode:            {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"  Duration:        {overall_elapsed:.1f}s")
    print(f"  Groups:          {len(unique_groups_sorted)}")
    print(f"  Trading days:    {len(trading_days)}")
    print(f"  Total writes:    {total_writes}")
    print(f"  Total failures:  {total_failures}")

    print(f"\n  {BOLD}Per-group breakdown:{RESET}")
    print(f"  {'Group':<50s}  {'Written':>7s}  {'Skip':>4s}  {'Fail':>4s}  {'Time':>6s}")
    print(f"  {'-' * 50}  {'-' * 7}  {'-' * 4}  {'-' * 4}  {'-' * 6}")
    for gname, gdata in results.items():
        w = gdata["days_written"]
        s = gdata["days_skipped"]
        f = gdata["days_failed"]
        t = gdata["elapsed_seconds"]
        color = GREEN if f == 0 and w > 0 else (RED if f > 0 else YELLOW)
        print(f"  {gname[:50]:<50s}  {color}{w:>7d}{RESET}  {s:>4d}  {f:>4d}  {t:>5.1f}s")

    if total_failures > 0:
        print(f"\n  {RED}WARNING: {total_failures} write(s) failed -- "
              f"check IAM permissions and table configuration{RESET}")
    elif total_writes == 0 and not dry_run:
        print(f"\n  {YELLOW}WARNING: Zero records written -- all days produced no data{RESET}")
    elif dry_run:
        print(f"\n  {YELLOW}DRY RUN -- no records were written to DynamoDB{RESET}")
    else:
        print(f"\n  {GREEN}All records written successfully{RESET}")

    # ---- Verification: re-read from DynamoDB ----
    if not dry_run and total_writes > 0:
        print(f"\n{BOLD}  Verification (re-reading from DynamoDB):{RESET}")
        from engines.dsl.operators.group_cache_lookup import lookup_historical_returns

        for gname, gdata in results.items():
            gid = gdata["group_id"]
            returns = lookup_historical_returns(
                group_id=gid,
                lookback_days=lookback_days,
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
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --dry-run
  poetry run python scripts/backfill_group_cache.py ftl_starburst.clj --group "WYLD*"
        """,
    )
    parser.add_argument(
        "strategy_file",
        help="Path to .clj strategy file (absolute, relative, or just filename)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=45,
        help="Calendar days to backfill (default: 45)",
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

    args = parser.parse_args()

    backfill_strategy_groups(
        clj_path=args.strategy_file,
        lookback_days=args.days,
        dry_run=args.dry_run,
        group_patterns=args.groups,
    )


if __name__ == "__main__":
    main()
