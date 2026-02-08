#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Full debug script for the FTL Starburst strategy.

Runs ftl_starburst.clj through the DSL engine with debug mode ON, then
traces every major decision branch showing computed indicator values,
filter/ranking outcomes, and the final allocation decomposed by sub-strategy.

ACTUAL top-level structure (verified from CLJ file):

    defsymphony "FTL Starburst | Interstellar Mods"
      weight-equal [                              <-- equal-weights 3 filters
        filter(moving-average-return w=10, select-bottom 1)
          [WYLD combo, Walter's, NOVA]            <-- picks lowest MAR
        filter(rsi w=10, select-bottom 1)
          [WYLD combo, Walter's, NOVA]            <-- picks lowest RSI
        filter(stdev-return w=10, select-bottom 1)
          [WYLD combo, Walter's, NOVA]            <-- picks lowest stdev
      ]

    Each filter evaluates the SAME 3 sub-strategies but picks the
    lowest-scoring one by a different metric. The 3 results are then
    weight-equal merged at 1/3 each.

    Inside each filter's sub-tree:
      WYLD = mean-reversion cascade (YINN/YANG, LABU/LABD, DRV/DRN) with
             Overcompensating Frontrunner fallback
      Walter's = KMLM|Tech + Modified Foreign Rat + JRT
      NOVA = RSI cascade checking QQQE/VTV/VOX/TECL/VOOG/VOOV/XLP thresholds

Usage:
    poetry run python scripts/debug_ftl_starburst.py
    poetry run python scripts/debug_ftl_starburst.py --as-of 2026-02-06
    poetry run python scripts/debug_ftl_starburst.py --as-of yesterday --json

"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("GROUP_HISTORY_TABLE", "alchemiser-dev-group-history")

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
STRATEGY_WORKER_PATH = PROJECT_ROOT / "functions" / "strategy_worker"
SHARED_LAYER_PATH = PROJECT_ROOT / "layers" / "shared"
STRATEGIES_PATH = SHARED_LAYER_PATH / "the_alchemiser" / "shared" / "strategies"

sys.path.insert(0, str(STRATEGY_WORKER_PATH))
sys.path.insert(0, str(SHARED_LAYER_PATH))

# FTL Starburst is deeply nested -- match Lambda handler recursion limit.
sys.setrecursionlimit(10000)

# Suppress noisy structlog output during evaluation.
import logging as _logging

_logging.getLogger("strategy_v2").setLevel(_logging.WARNING)
_logging.getLogger("the_alchemiser").setLevel(_logging.WARNING)

DSL_FILE = "ftl_starburst.clj"

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

# ---------------------------------------------------------------------------
# Top-level filter metrics (order must match the CLJ file structure).
# Each filter selects the bottom-1 group from [WYLD, Walter's, NOVA].
# ---------------------------------------------------------------------------
TOP_LEVEL_FILTER_METRICS = [
    "moving-average-return",
    "rsi",
    "stdev-return",
]

# Expected per-block filter count (9 OFR pairs + 1 MAX DD + 2 Walter's + 1 top-level = ~30)
FILTERS_PER_BLOCK = 30

# Group names as they appear in the DSL
GROUP_WYLD = "WYLD Mean Reversion Combo v2 w/ Overcompensating Frontrunner [FTL]"
GROUP_WALTERS = "Walter's Champagne and CocaineStrategies"
GROUP_NOVA = "NOVA | (multiple TQQQ, one crypto) KMLM switcher (single pops) MonkeyBusiness  WM74|"

GROUP_SHORT_NAMES = {
    GROUP_WYLD: "WYLD",
    GROUP_WALTERS: "Walter's",
    GROUP_NOVA: "NOVA",
}

# NOVA RSI cascade thresholds from the CLJ
NOVA_RSI_CASCADE = [
    ("QQQE", 79),
    ("VTV", 79),
    ("VOX", 79),
    ("TECL", 79),
    ("VOOG", 79),
    ("VOOV", 79),
    ("XLP", 75),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_date(date_str: str) -> date:
    """Parse date string to a ``date`` object.

    Args:
        date_str: Date in YYYY-MM-DD, 'yesterday', or 'today'.

    Returns:
        Parsed date.

    """
    low = date_str.lower()
    if low == "yesterday":
        return date.today() - timedelta(days=1)
    if low == "today":
        return date.today()
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _pct(value: float) -> str:
    """Format a weight as a percentage string."""
    return f"{value * 100:.1f}%"


def _dollar(value: float) -> str:
    """Format a dollar amount."""
    return f"${value:,.2f}"


# ---------------------------------------------------------------------------
# Historical adapter (date-filtered wrapper)
# ---------------------------------------------------------------------------
def _build_market_data_adapter(
    as_of_date: date | None,
) -> Any:
    """Build either a live or historical-cutoff market data adapter.

    Args:
        as_of_date: If provided, only deliver bars up to this date.

    Returns:
        A MarketDataPort implementation.

    """
    if as_of_date is None:
        from the_alchemiser.shared.data_v2.cached_market_data_adapter import (
            CachedMarketDataAdapter,
        )

        return CachedMarketDataAdapter()

    # Historical cutoff adapter
    import pandas as pd

    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.types.market_data import BarModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol

    class _HistoricalAdapter(MarketDataPort):
        """MarketDataPort that filters bars to a cutoff date."""

        def __init__(self, cutoff: date) -> None:
            self.cutoff = cutoff
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

    return _HistoricalAdapter(as_of_date)


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------
def run_ftl_starburst(
    as_of_date: date | None = None,
    output_json: bool = False,
) -> dict[str, Any]:
    """Run FTL Starburst with full debug tracing.

    Args:
        as_of_date: Optional historical date cutoff.
        output_json: If True, dump machine-readable JSON at the end.

    Returns:
        Dict with allocation, decision_path, debug_traces, filter_traces.

    """
    # Silence structlog before any engine imports to suppress startup noise.
    import structlog as _structlog

    _structlog.configure(wrapper_class=_structlog.make_filtering_bound_logger(_logging.INFO))

    from engines.dsl.engine import DslEngine

    adapter = _build_market_data_adapter(as_of_date)

    engine = DslEngine(
        strategy_config_path=STRATEGIES_PATH,
        market_data_adapter=adapter,
        debug_mode=True,
    )

    label = f" (as-of {as_of_date})" if as_of_date else ""
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  FTL STARBURST -- Full Debug Trace{label}{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    # If historical, verify data availability on a couple of key symbols.
    if as_of_date is not None:
        print(f"\n{DIM}Data cutoff verification:{RESET}")
        for sym in ("SPY", "QQQ", "XLK", "KMLM", "FXI", "EEM"):
            try:
                bars = adapter.get_bars(
                    type("S", (), {"__str__": lambda s: sym})(), "2Y", "1Day"
                )
                last = bars[-1].timestamp.date() if bars else None
                status = f"{GREEN}OK{RESET}" if last else f"{RED}NO DATA{RESET}"
                print(f"  {sym:6s} last bar = {last}  {status}")
            except Exception as exc:
                print(f"  {sym:6s} ERROR: {exc}")
        print()

    # ---- Run strategy ----
    correlation_id = f"debug-ftl-starburst-{datetime.now(UTC).strftime('%H%M%S')}"
    print(f"\n{DIM}Running strategy engine ...{RESET}", end="", flush=True)
    allocation, trace = engine.evaluate_strategy(DSL_FILE, correlation_id)
    print(f" done.{RESET}")

    # Collect debug artefacts
    debug_traces: list[dict[str, Any]] = list(engine.evaluator.debug_traces)
    decision_path: list[dict[str, Any]] = list(engine.evaluator.decision_path)
    filter_traces: list[dict[str, Any]] = list(engine.evaluator.filter_traces)

    weights = {k: float(v) for k, v in allocation.target_weights.items()}

    # ------------------------------------------------------------------
    # 1. Strategy architecture (the actual CLJ structure)
    # ------------------------------------------------------------------
    _print_architecture_summary(filter_traces)

    # ------------------------------------------------------------------
    # 2. NOVA RSI cascade (the key divergence point)
    # ------------------------------------------------------------------
    _print_nova_rsi_cascade(debug_traces)

    # ------------------------------------------------------------------
    # 3. Top-level group selection (3 filters x 3 groups)
    # ------------------------------------------------------------------
    _print_top_level_group_selection(filter_traces)

    # ------------------------------------------------------------------
    # 4. Overcompensating Frontrunner (OFR) summary
    # ------------------------------------------------------------------
    _print_ofr_summary(filter_traces)

    # ------------------------------------------------------------------
    # 5. Decision path (if-branch trace) -- deduplicated
    # ------------------------------------------------------------------
    _print_decision_path(decision_path, debug_traces)

    # ------------------------------------------------------------------
    # 6. Filter / ranking traces (full, for deep debugging)
    # ------------------------------------------------------------------
    _print_filter_traces(filter_traces)

    # ------------------------------------------------------------------
    # 7. Final allocation summary (Composer-style)
    # ------------------------------------------------------------------
    _print_allocation_summary(weights, as_of_date)

    # ------------------------------------------------------------------
    # 8. Divergence analysis
    # ------------------------------------------------------------------
    _print_divergence_analysis(weights, filter_traces, debug_traces)

    if output_json:
        print(f"\n{DIM}--- JSON dump ---{RESET}")
        print(
            json.dumps(
                {
                    "allocation": weights,
                    "decision_path_count": len(decision_path),
                    "debug_trace_count": len(debug_traces),
                    "filter_trace_count": len(filter_traces),
                },
                indent=2,
            )
        )

    return {
        "allocation": weights,
        "decision_path": decision_path,
        "debug_traces": debug_traces,
        "filter_traces": filter_traces,
    }


# ---------------------------------------------------------------------------
# Printers
# ---------------------------------------------------------------------------


def _get_filter_indicator(ft: dict[str, Any]) -> str:
    """Extract the actual indicator function name from a filter trace."""
    condition = ft.get("condition", {})
    # The indicator name is stored under "func" (e.g., "rsi", "stdev-return")
    func = condition.get("func", condition.get("indicator_type", condition.get("type", "?")))
    return str(func)


def _get_filter_window(ft: dict[str, Any]) -> Any:
    """Extract the filter window parameter."""
    condition = ft.get("condition", {})
    params = condition.get("params", {})
    if isinstance(params, dict):
        return params.get("window", "?")
    return condition.get("window", "?")


def _is_top_level_group_filter(ft: dict[str, Any]) -> bool:
    """Check if a filter trace is a top-level group selection (3 portfolio candidates)."""
    if ft.get("mode") != "portfolio":
        return False
    candidates = ft.get("scored_candidates", [])
    if len(candidates) != 3:
        return False
    names = {c.get("candidate_name", "") for c in candidates}
    known = {GROUP_WYLD, GROUP_WALTERS, GROUP_NOVA}
    # All 3 must be present (names may have slight variations)
    return len(names & known) >= 2


def _is_ofr_max_dd_filter(ft: dict[str, Any]) -> bool:
    """Check if a filter trace is an OFR MAX DD portfolio selection."""
    if ft.get("mode") != "portfolio":
        return False
    candidates = ft.get("scored_candidates", [])
    if len(candidates) < 5:
        return False
    names = [c.get("candidate_name", "") for c in candidates]
    return any("MAX DD:" in n for n in names)


def _short_group_name(name: str) -> str:
    """Shorten a group name for display."""
    for full, short in GROUP_SHORT_NAMES.items():
        if full in name or name in full:
            return short
    if "WYLD" in name:
        return "WYLD"
    if "Walter" in name:
        return "Walter's"
    if "NOVA" in name:
        return "NOVA"
    return name[:30]


def _print_architecture_summary(filter_traces: list[dict[str, Any]]) -> None:
    """Print the actual CLJ architecture structure."""
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  STRATEGY ARCHITECTURE{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print()
    print(f"  defsymphony \"FTL Starburst | Interstellar Mods\"")
    print(f"    weight-equal [               {DIM}(3 filter blocks, 1/3 each){RESET}")

    # Find the 3 top-level group filters
    top_filters = [ft for ft in filter_traces if _is_top_level_group_filter(ft)]
    block_num = 0
    for ft in top_filters:
        block_num += 1
        indicator = _get_filter_indicator(ft)
        window = _get_filter_window(ft)
        candidates = ft.get("scored_candidates", [])
        selected = ft.get("selected_candidate_ids", [])

        # Find winner
        winner_name = "?"
        winner_symbols: list[str] = []
        for c in candidates:
            if c.get("candidate_id", "") in selected:
                winner_name = _short_group_name(c.get("candidate_name", "?"))
                winner_symbols = c.get("symbols_sample", [])
                break

        sym_str = ", ".join(winner_symbols) if winner_symbols else "?"
        print(f"      [{block_num}] filter({indicator} w={window}, select-bottom 1)")
        print(f"          {GREEN}-> {winner_name}{RESET} [{sym_str}]")

    if not top_filters:
        print(f"      {RED}(no top-level group filters found in traces){RESET}")
    print(f"    ]")
    print()


def _print_nova_rsi_cascade(debug_traces: list[dict[str, Any]]) -> None:
    """Print the NOVA RSI cascade values in a clear table (once, not 3x)."""
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  NOVA RSI CASCADE{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print()
    print(f"  When any RSI check is True, NOVA routes to UVXY (sell signal).")
    print(f"  When all are False, NOVA continues to TQQQ/alternate branches.")
    print()

    # Collect first occurrence of each RSI check from debug traces
    seen_symbols: set[str] = set()
    rsi_results: list[tuple[str, float, float, bool]] = []

    for t in debug_traces:
        left_expr = t.get("left_expr", "")
        if not left_expr.startswith("rsi("):
            continue
        # Extract symbol from "rsi(XLP)"
        sym = left_expr.replace("rsi(", "").rstrip(")")
        if sym in seen_symbols:
            continue
        seen_symbols.add(sym)

        left_val = t.get("left_value", 0.0)
        right_val = t.get("right_value", 0.0)
        result = t.get("result", False)
        rsi_results.append((sym, float(left_val), float(right_val), bool(result)))

    # Display in cascade order
    print(f"  {'Symbol':<8s}  {'RSI(10)':<12s}  {'Threshold':<10s}  {'Result':<10s}  {'Action'}")
    print(f"  {'------':<8s}  {'------':<12s}  {'---------':<10s}  {'------':<10s}  {'------'}")

    hit_uvxy = False
    for sym, threshold in NOVA_RSI_CASCADE:
        # Find matching result
        match = None
        for s, rsi_val, thr, res in rsi_results:
            if s == sym:
                match = (rsi_val, thr, res)
                break

        if match:
            rsi_val, thr, result = match
            colour = RED if result else GREEN
            result_str = f"{colour}{'TRUE' if result else 'False'}{RESET}"
            margin = rsi_val - thr
            margin_str = f"({'+' if margin >= 0 else ''}{margin:.2f})"
            if result and not hit_uvxy:
                action = f"{RED}-> UVXY{RESET}"
                hit_uvxy = True
            elif result:
                action = f"{DIM}(already triggered){RESET}"
            else:
                action = f"{DIM}pass{RESET}"
            print(f"  {sym:<8s}  {rsi_val:<12.4f}  > {thr:<8.0f}  {result_str:<20s}  {action}  {DIM}{margin_str}{RESET}")
        else:
            print(f"  {sym:<8s}  {DIM}(not found in traces){RESET}")

    if not hit_uvxy:
        print(f"\n  {GREEN}All RSI checks False -> NOVA continues to TQQQ/alternate path{RESET}")
    else:
        print(f"\n  {RED}RSI cascade triggered -> NOVA picks UVXY{RESET}")

    # Show what Composer expects
    if COMPOSER_EXPECTED.get("TQQQ", 0) > 0.5:
        print(f"\n  {YELLOW}COMPOSER comparison: NOVA should pick TQQQ (66.6% in Composer)")
        print(f"  This means Composer's RSI values must ALL be below threshold.{RESET}")


def _print_top_level_group_selection(filter_traces: list[dict[str, Any]]) -> None:
    """Print the 3 top-level group selection filters clearly."""
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  TOP-LEVEL GROUP SELECTION (1/3 weight each){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print()

    top_filters = [ft for ft in filter_traces if _is_top_level_group_filter(ft)]

    for block_idx, ft in enumerate(top_filters):
        indicator = _get_filter_indicator(ft)
        window = _get_filter_window(ft)
        candidates = ft.get("scored_candidates", [])
        selected_ids = ft.get("selected_candidate_ids", [])

        print(f"  {BOLD}Block {block_idx + 1}/3:{RESET} filter({CYAN}{indicator}{RESET} w={window}, "
              f"select-bottom 1)")
        print()

        for c in candidates:
            name = _short_group_name(c.get("candidate_name", "?"))
            score = c.get("score", 0.0)
            is_selected = c.get("candidate_id", "") in selected_ids
            symbols = c.get("symbols_sample", [])
            sym_str = ", ".join(symbols[:5]) if symbols else "?"

            marker = f" {GREEN}<< SELECTED{RESET}" if is_selected else ""
            score_str = f"{score:>12.6f}" if isinstance(score, float) else str(score)

            if is_selected:
                print(f"    {GREEN}{name:<12s}{RESET} score={score_str}  [{sym_str}]{marker}")
            else:
                print(f"    {DIM}{name:<12s}{RESET} score={score_str}  {DIM}[{sym_str}]{RESET}")

        # Show returns_available info from scoring logs
        for c in candidates:
            if c.get("candidate_id", "") in selected_ids:
                print(f"    {DIM}Winner resolves to: {', '.join(c.get('symbols_sample', []))}{RESET}")
        print()

    if not top_filters:
        print(f"  {RED}No top-level group filters found.{RESET}")
        print(f"  {DIM}Expected 3 filters with 3 portfolio candidates each.{RESET}")


def _print_ofr_summary(filter_traces: list[dict[str, Any]]) -> None:
    """Print a summary of the Overcompensating Frontrunner MAX DD selections."""
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  OVERCOMPENSATING FRONTRUNNER (OFR) -- MAX DD SELECT-TOP 1{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print()

    ofr_filters = [ft for ft in filter_traces if _is_ofr_max_dd_filter(ft)]

    if not ofr_filters:
        print(f"  {DIM}No OFR MAX DD filters found.{RESET}")
        return

    # All OFR instances should produce identical results (same market data).
    # Show only the first one as representative, note duplicates.
    first = ofr_filters[0]
    candidates = first.get("scored_candidates", [])
    selected_ids = first.get("selected_candidate_ids", [])

    print(f"  8 TQQQ-vs-X pairs scored by stdev-return, then select-top 1 by score:")
    print(f"  (higher score = more volatile = selected as hedge)")
    print()

    for c in candidates:
        name = c.get("candidate_name", "?")
        score = c.get("score", 0.0)
        is_selected = c.get("candidate_id", "") in selected_ids
        symbols = c.get("symbols_sample", [])
        sym_str = ", ".join(symbols) if symbols else "?"

        marker = f" {GREEN}<< SELECTED{RESET}" if is_selected else ""
        score_str = f"{score:>12.4f}" if isinstance(score, float) else str(score)

        if is_selected:
            print(f"    {GREEN}{name:<30s}{RESET} score={score_str}  [{sym_str}]{marker}")
        else:
            print(f"    {DIM}{name:<30s}{RESET} score={score_str}  {DIM}[{sym_str}]{RESET}")

    print(f"\n  {DIM}(Appears {len(ofr_filters)} times total -- once per WYLD sub-group per block, all identical){RESET}")


def _print_decision_path(
    decision_path: list[dict[str, Any]],
    debug_traces: list[dict[str, Any]],
) -> None:
    """Print unique if-branch decisions (deduplicated across blocks)."""
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  DECISION PATH ({len(decision_path)} total, showing unique){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    # Deduplicate: same condition + result = skip
    seen: set[tuple[str, bool]] = set()
    unique_count = 0
    for i, node in enumerate(decision_path, 1):
        cond = node.get("condition", "?")
        result = node.get("result")
        branch = node.get("branch", "?")

        key = (cond, bool(result))
        if key in seen:
            continue
        seen.add(key)
        unique_count += 1

        colour = GREEN if result else RED
        sym = "T" if result else "F"
        print(f"\n  {DIM}[{i:>3}]{RESET} {cond}")
        print(f"       {colour}{sym}{RESET} -> branch: {CYAN}{branch}{RESET}")

    print(f"\n  {DIM}({unique_count} unique decisions from {len(decision_path)} total){RESET}")


def _print_filter_traces(filter_traces: list[dict[str, Any]]) -> None:
    """Print filter/ranking traces with proper indicator names."""
    if not filter_traces:
        return

    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  ALL FILTER TRACES ({len(filter_traces)} filters){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    for i, ft in enumerate(filter_traces, 1):
        mode = ft.get("mode", "?")
        order = ft.get("order", "?")
        limit = ft.get("limit", "?")
        candidates = ft.get("scored_candidates", [])
        selected_ids = ft.get("selected_candidate_ids", [])

        indicator = _get_filter_indicator(ft)
        window = _get_filter_window(ft)

        # Mark top-level and OFR filters
        tag = ""
        if _is_top_level_group_filter(ft):
            tag = f" {YELLOW}[TOP-LEVEL]{RESET}"
        elif _is_ofr_max_dd_filter(ft):
            tag = f" {MAGENTA}[OFR MAX-DD]{RESET}"

        print(f"\n  {DIM}[{i:>3}]{RESET} {MAGENTA}filter{RESET} "
              f"select-{order} {limit} by {CYAN}{indicator}{RESET}(window={window})  "
              f"[{mode} mode]{tag}")

        # Show all candidates scored
        for c in candidates:
            name = c.get("candidate_name") or c.get("candidate_id", "?")
            score = c.get("score")
            is_selected = c.get("candidate_id", "") in selected_ids
            marker = f"{GREEN}<<{RESET}" if is_selected else ""
            score_str = f"{score:.6f}" if isinstance(score, float) else str(score)
            display_name = _short_group_name(name) if mode == "portfolio" else name
            print(f"       {display_name:30s}  score={score_str}  {marker}")


def _print_debug_traces(debug_traces: list[dict[str, Any]]) -> None:
    """Print raw comparison traces."""
    if not debug_traces:
        return

    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  RAW COMPARISON TRACES ({len(debug_traces)} comparisons){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    for i, t in enumerate(debug_traces, 1):
        left_expr = t.get("left_expr", "?")
        left_val = t.get("left_value", "?")
        op = t.get("operator", "?")
        right_expr = t.get("right_expr", "?")
        right_val = t.get("right_value", "?")
        result = t.get("result", "?")

        colour = GREEN if result else RED
        left_str = f"{left_val:.4f}" if isinstance(left_val, float) else str(left_val)
        right_str = f"{right_val:.4f}" if isinstance(right_val, float) else str(right_val)

        print(f"\n  {DIM}[{i:>3}]{RESET} {left_expr} {op} {right_expr}")
        print(f"       {left_str} {op} {right_str} = {colour}{result}{RESET}")


# Composer expected allocation for 2026-02-06 (provided as reference).
# Update this dict when you have new Composer data to compare against.
COMPOSER_EXPECTED: dict[str, float] = {
    "TQQQ": 0.666,
    "TECS": 0.111,
    "EDC": 0.109,
    "COST": 0.050,
    "GE": 0.037,
    "LLY": 0.014,
    "NVO": 0.010,
}
COMPOSER_DATE = "2026-02-06"


def _print_allocation_summary(
    weights: dict[str, float],
    as_of_date: date | None,
) -> None:
    """Print the final allocation alongside Composer expected values."""
    date_label = str(as_of_date) if as_of_date else "today"
    total = sum(weights.values())
    show_composer = str(as_of_date) == COMPOSER_DATE if as_of_date else False

    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  FINAL ALLOCATION -- Simulated Holdings (close {date_label}){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print()

    if show_composer:
        print(f"  {'Symbol':<8s}  {'Ours':>10s}  {'Composer':>10s}  {'Delta':>8s}  {'Match'}")
        print(f"  {'------':<8s}  {'--------':>10s}  {'--------':>10s}  {'-----':>8s}  {'-----'}")
    else:
        print(f"  {'Symbol':<8s}  {'Allocation':>12s}")
        print(f"  {'------':<8s}  {'----------':>12s}")

    all_syms = sorted(
        set(list(weights.keys()) + (list(COMPOSER_EXPECTED.keys()) if show_composer else [])),
        key=lambda s: -(weights.get(s, 0.0)),
    )

    for sym in all_syms:
        ours = weights.get(sym, 0.0)
        bar_len = int(ours * 50)
        bar = CYAN + "|" * bar_len + RESET

        if show_composer:
            comp = COMPOSER_EXPECTED.get(sym, 0.0)
            delta = ours - comp
            match = abs(delta) < 0.02
            delta_colour = GREEN if match else RED
            match_str = f"{GREEN}OK{RESET}" if match else f"{RED}MISMATCH{RESET}"
            delta_str = f"{delta_colour}{delta:+.1%}{RESET}"
            print(f"  {sym:<8s}  {_pct(ours):>10s}  {_pct(comp):>10s}  {delta_str:>18s}  {match_str}  {bar}")
        else:
            print(f"  {sym:<8s}  {_pct(ours):>12s}  {bar}")

    print(f"  {'':8s}  {'----------':>12s}")
    print(f"  {'TOTAL':<8s}  {_pct(total):>12s}")

    if abs(total - 1.0) > 0.02:
        print(f"\n  {YELLOW}WARNING: weights sum to {total:.4f}, expected ~1.0{RESET}")

    if show_composer:
        mismatches = []
        for sym in all_syms:
            ours = weights.get(sym, 0.0)
            comp = COMPOSER_EXPECTED.get(sym, 0.0)
            if abs(ours - comp) >= 0.02:
                mismatches.append(sym)
        if mismatches:
            print(f"\n  {RED}SIGNAL DISCREPANCY on: {', '.join(mismatches)}{RESET}")
        else:
            print(f"\n  {GREEN}All allocations match Composer within 2% tolerance.{RESET}")


def _print_divergence_analysis(
    weights: dict[str, float],
    filter_traces: list[dict[str, Any]],
    debug_traces: list[dict[str, Any]],
) -> None:
    """Print detailed divergence analysis vs Composer."""
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  DIVERGENCE ANALYSIS vs COMPOSER ({COMPOSER_DATE}){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    # 1. Architecture explanation
    print(f"\n  {BOLD}Architecture:{RESET}")
    print(f"    weight-equal of 3 filters, each selecting bottom-1 from")
    print(f"    [WYLD, Walter's, NOVA] by a different metric.")
    print()

    # 2. What Composer shows
    print(f"  {BOLD}Composer allocation ({COMPOSER_DATE}):{RESET}")
    print(f"    TQQQ 66.6% = 2 of 3 filters picked a group resolving to TQQQ")
    print(f"    Walter's 33.3% = 1 of 3 filters picked Walter's")
    print(f"    This means: in Composer, both WYLD and NOVA resolve to TQQQ,")
    print(f"    and 2 of 3 filters pick TQQQ-resolving groups.")
    print()

    # 3. What our engine shows
    print(f"  {BOLD}Our engine allocation:{RESET}")
    top_filters = [ft for ft in filter_traces if _is_top_level_group_filter(ft)]
    for block_idx, ft in enumerate(top_filters):
        indicator = _get_filter_indicator(ft)
        selected_ids = ft.get("selected_candidate_ids", [])
        candidates = ft.get("scored_candidates", [])
        winner = "?"
        winner_syms: list[str] = []
        for c in candidates:
            if c.get("candidate_id", "") in selected_ids:
                winner = _short_group_name(c.get("candidate_name", "?"))
                winner_syms = c.get("symbols_sample", [])
                break
        sym_str = ", ".join(winner_syms) if winner_syms else "?"
        print(f"    Block {block_idx + 1} ({indicator}): {winner} -> [{sym_str}]")
    print()

    # 4. Root cause analysis
    print(f"  {BOLD}Root Cause Analysis:{RESET}")
    print()

    # Check NOVA RSI divergence
    nova_picks_uvxy = weights.get("UVXY", 0.0) > 0.1
    if nova_picks_uvxy:
        # Find which NOVA cascade RSI triggered it (XLP, QQQE, VTV, etc.)
        nova_cascade_syms = {sym for sym, _ in NOVA_RSI_CASCADE}
        for t in debug_traces:
            left_expr = t.get("left_expr", "")
            if not left_expr.startswith("rsi("):
                continue
            # Only look at NOVA cascade RSI checks (XLP, QQQE, VTV, etc.)
            sym = left_expr.replace("rsi(", "").rstrip(")")
            if sym not in nova_cascade_syms:
                continue
            right_val = t.get("right_value", 0.0)
            # Only match numeric threshold comparisons (not rsi-vs-rsi)
            if not isinstance(right_val, (int, float)) or right_val < 10:
                continue
            if t.get("result"):
                rsi_val = t.get("left_value", 0.0)
                threshold = right_val
                margin = float(rsi_val) - float(threshold)
                print(f"  {RED}[DIVERGENCE 1] NOVA RSI cascade triggers UVXY{RESET}")
                print(f"    rsi({sym}) = {float(rsi_val):.4f} > {float(threshold):.0f}  (margin: +{margin:.2f})")
                print(f"    In Composer, NOVA picks TQQQ (all RSI checks must be False).")
                print(f"    Possible causes:")
                print(f"      - RSI calculation differs (period, data source, adjusted close)")
                print(f"      - Data feed mismatch (Alpaca S3 cache vs Composer's data)")
                print(f"      - RSI threshold transcription error in CLJ file")
                print()
                break

    # Check group selection divergence
    our_tqqq = weights.get("TQQQ", 0.0)
    comp_tqqq = COMPOSER_EXPECTED.get("TQQQ", 0.0)
    if abs(our_tqqq - comp_tqqq) > 0.1:
        print(f"  {RED}[DIVERGENCE 2] Group selection scoring differs{RESET}")
        print(f"    Ours: TQQQ = {_pct(our_tqqq)}, Composer: TQQQ = {_pct(comp_tqqq)}")

        # Show DynamoDB return count
        for ft in top_filters:
            candidates = ft.get("scored_candidates", [])
            for c in candidates:
                # Check if symbols_sample hints at available data
                pass

        print(f"    The portfolio-level metrics (MAR, RSI, stdev-return) are computed")
        print(f"    from DynamoDB-cached historical returns. With limited history,")
        print(f"    scores will diverge from Composer's full-history computations.")
        print()

    # Check OFR divergence
    ofr_filters = [ft for ft in filter_traces if _is_ofr_max_dd_filter(ft)]
    if ofr_filters:
        first_ofr = ofr_filters[0]
        selected_ids = first_ofr.get("selected_candidate_ids", [])
        for c in first_ofr.get("scored_candidates", []):
            if c.get("candidate_id", "") in selected_ids:
                ofr_sym = ", ".join(c.get("symbols_sample", ["?"]))
                if "UVXY" in ofr_sym:
                    print(f"  {YELLOW}[NOTE] OFR selects UVXY (stdev-return select-top-1){RESET}")
                    print(f"    UVXY has highest stdev-return -> selected as hedge.")
                    print(f"    This feeds into WYLD's output, which is then")
                    print(f"    scored against Walter's and NOVA by the top-level filter.")
                    print()
                break

    # Summary
    print(f"  {BOLD}Investigation priorities:{RESET}")
    print(f"    1. Verify RSI(10) calculation matches Composer's (check period/data)")
    print(f"    2. Check DynamoDB returns_available count (need > 20 for stable scores)")
    print(f"    3. Compare XLP close prices between our S3 cache and Composer's data")
    print(f"    4. Consider whether Composer uses adjusted close vs raw close for RSI")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Full debug trace for the FTL Starburst strategy",
    )
    parser.add_argument(
        "--as-of",
        dest="as_of",
        help="Market data date cutoff (YYYY-MM-DD, 'yesterday', 'today'). "
        "Default: use latest cached data.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Dump machine-readable JSON summary at end",
    )
    args = parser.parse_args()

    as_of_date: date | None = parse_date(args.as_of) if args.as_of else None

    try:
        run_ftl_starburst(as_of_date=as_of_date, output_json=args.json)
    except Exception as exc:
        print(f"\n{RED}ERROR: {type(exc).__name__}: {exc}{RESET}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
