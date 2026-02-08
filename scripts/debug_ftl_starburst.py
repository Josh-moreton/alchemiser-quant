#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Full debug script for the FTL Starburst strategy.

Runs ftl_starburst.clj through the DSL engine with debug mode ON, then
traces every major decision branch showing computed indicator values,
filter/ranking outcomes, and the final allocation decomposed by sub-strategy.

The top-level structure of FTL Starburst is:
    weight-equal [
        1/3  FTL Starburst (WYLD Mean Reversion Combo, filter select-bottom 1)
        1/3  Walter's Champagne & Cocaine (KMLM|Tech, Modified Foreign Rat, JRT)
        1/3  NOVA (MonkeyBusiness RSI cascade -> TQQQ / UVXY)
    ]

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
# Sub-strategy labels used in the DSL (for trace matching)
# ---------------------------------------------------------------------------
TOP_LEVEL_GROUPS = [
    "FTL Starburst",
    " Walter's Champagne and CocaineStrategies",
    "NOVA",
]

WALTERS_SUB_GROUPS = [
    "KMLM | Technology",
    "Modified Foreign Rat",
    "JRT",
]

WYLD_SUB_GROUPS = [
    "YINN YANG Mean Reversion",
    "LABU LABD Mean Reversion",
    "DRV DRN Mean Reversion",
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

    _structlog.configure(wrapper_class=_structlog.make_filtering_bound_logger(_logging.WARNING))

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
    # 1. Decision path (if-branch trace) -- enriched with raw values
    # ------------------------------------------------------------------
    _print_decision_path(decision_path, debug_traces)

    # ------------------------------------------------------------------
    # 2. Filter / ranking traces
    # ------------------------------------------------------------------
    _print_filter_traces(filter_traces)

    # ------------------------------------------------------------------
    # 3. Debug traces (individual comparisons)
    # ------------------------------------------------------------------
    _print_debug_traces(debug_traces)

    # ------------------------------------------------------------------
    # 4. Final allocation summary (Composer-style)
    # ------------------------------------------------------------------
    _print_allocation_summary(weights, as_of_date)

    # ------------------------------------------------------------------
    # 5. Sub-strategy decomposition
    # ------------------------------------------------------------------
    _print_sub_strategy_decomposition(weights, decision_path)

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
def _print_decision_path(
    decision_path: list[dict[str, Any]],
    debug_traces: list[dict[str, Any]],
) -> None:
    """Print every if-branch decision with actual computed indicator values.

    The decision_path and debug_traces are NOT index-aligned (decision path
    captures bottom-up from recursion, debug traces capture top-down). We
    show values from the raw traces section instead of cross-referencing.
    """
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  DECISION PATH ({len(decision_path)} if-branches evaluated){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    for i, node in enumerate(decision_path, 1):
        cond = node.get("condition", "?")
        result = node.get("result")
        branch = node.get("branch", "?")

        colour = GREEN if result else RED
        sym = "T" if result else "F"
        print(f"\n  {DIM}[{i:>3}]{RESET} {cond}")
        print(f"       {colour}{sym}{RESET} -> branch: {CYAN}{branch}{RESET}")


def _print_filter_traces(filter_traces: list[dict[str, Any]]) -> None:
    """Print filter/ranking traces."""
    if not filter_traces:
        return

    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  FILTER / RANKING TRACES ({len(filter_traces)} filters){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    for i, ft in enumerate(filter_traces, 1):
        mode = ft.get("mode", "?")
        order = ft.get("order", "?")
        limit = ft.get("limit", "?")
        condition = ft.get("condition", {})
        candidates = ft.get("scored_candidates", [])
        selected_ids = ft.get("selected_candidate_ids", [])

        indicator = condition.get("indicator_type", condition.get("type", "?"))
        window = condition.get("window", condition.get("params", {}).get("window", "?"))

        print(f"\n  {DIM}[{i:>3}]{RESET} {MAGENTA}filter{RESET} "
              f"select-{order} {limit} by {indicator}(window={window})  [{mode} mode]")

        # Show all candidates scored
        for c in candidates:
            name = c.get("candidate_name") or c.get("candidate_id", "?")
            score = c.get("score")
            rank = c.get("rank", "?")
            is_selected = c.get("candidate_id", "") in selected_ids
            marker = f"{GREEN}<<{RESET}" if is_selected else ""
            score_str = f"{score:.6f}" if isinstance(score, float) else str(score)
            print(f"       rank {rank}: {name:30s}  score={score_str}  {marker}")


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
            print(f"  Check decision path above for divergent conditions.")
        else:
            print(f"\n  {GREEN}All allocations match Composer within 2% tolerance.{RESET}")


def _print_sub_strategy_decomposition(
    weights: dict[str, float],
    decision_path: list[dict[str, Any]],
) -> None:
    """Attempt to attribute symbols to the three top-level sub-strategies.

    This uses heuristics based on the known DSL structure:
    - FTL Starburst (1/3): WYLD mean reversion -> Overcompensating Frontrunner /
      WAM. Typically resolves to TQQQ.
    - Walter's Champagne (1/3): KMLM|Tech (TECL/TECS), Modified Foreign Rat
      (EDC/EDZ), JRT (LLY, NVO, COST, PGR||GE).
    - NOVA (1/3): RSI cascade, usually resolves to TQQQ or UVXY.

    """
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}  SUB-STRATEGY DECOMPOSITION (heuristic){RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")

    # Known symbol -> sub-strategy mapping based on the DSL structure.
    # JRT assets
    jrt_symbols = {"LLY", "NVO", "COST", "PGR", "GE"}
    # KMLM|Technology outcomes
    kmlm_tech_symbols = {"TECL", "TECS"}
    # Modified Foreign Rat outcomes
    foreign_rat_symbols = {"EDC", "EDZ"}
    # Mean reversion specific
    mean_rev_symbols = {"YINN", "YANG", "LABU", "LABD", "DRN", "DRV"}
    # NOVA volatility
    nova_vol_symbols = {"UVXY", "VIXY", "VIXM", "BTAL", "SPXL"}
    # WAM bear side
    wam_bear_symbols = {"SQQQ", "TECS", "DRV", "SRTY", "TMV", "PSQ", "DOG", "SH", "RWM", "TBF"}
    # WAM bull side
    wam_bull_symbols = {"TECL", "TQQQ", "DRN", "URTY", "SOXL", "EDC"}
    # Overcompensating Frontrunner
    frontrunner_symbols = {"UVXY", "SOXL", "FNGU", "UUP", "VDE", "SMH", "AVUV", "NAIL"}

    # TQQQ can come from NOVA (1/3) or FTL Starburst WYLD (1/3)
    # For simplicity, attribute 1/3 to each top-level group based on known allocation weights.
    third = Decimal("1") / Decimal("3")
    third_f = float(third)

    walters_weight = 0.0
    walters_syms: dict[str, float] = {}
    nova_weight = 0.0
    nova_syms: dict[str, float] = {}
    ftl_weight = 0.0
    ftl_syms: dict[str, float] = {}

    for sym, w in weights.items():
        if sym in jrt_symbols or sym in kmlm_tech_symbols or sym in foreign_rat_symbols:
            walters_syms[sym] = w
            walters_weight += w
        elif sym in mean_rev_symbols:
            ftl_syms[sym] = w
            ftl_weight += w
        elif sym in nova_vol_symbols:
            nova_syms[sym] = w
            nova_weight += w
        else:
            # Shared symbols like TQQQ, SQQQ, BIL -- split attribution
            # TQQQ is the most common shared symbol
            # Heuristic: if total weight is ~2/3 it spans two groups
            if w > third_f * 1.5:
                # Likely spans both FTL Starburst and NOVA
                ftl_syms[sym] = ftl_syms.get(sym, 0) + third_f
                ftl_weight += third_f
                nova_syms[sym] = nova_syms.get(sym, 0) + (w - third_f)
                nova_weight += w - third_f
            elif w > 0.01:
                # Could be from WAM inside FTL Starburst or NOVA
                # Default to FTL since WAM is nested inside WYLD
                ftl_syms[sym] = ftl_syms.get(sym, 0) + w
                ftl_weight += w

    # Print decomposition
    def _print_group(
        name: str,
        target_pct: float,
        actual_pct: float,
        syms: dict[str, float],
    ) -> None:
        colour = GREEN if abs(actual_pct - target_pct) < 0.05 else YELLOW
        print(f"\n  {BOLD}{name}{RESET}")
        print(f"    Target: {_pct(target_pct):<8s}  Actual: {colour}{_pct(actual_pct)}{RESET}")
        for s in sorted(syms, key=lambda x: -syms[x]):
            print(f"      {s:<8s} {_pct(syms[s]):>8s}")

    _print_group("1/3 -- FTL Starburst (WYLD Mean Reversion)", third_f, ftl_weight, ftl_syms)
    _print_group("1/3 -- Walter's Champagne & Cocaine", third_f, walters_weight, walters_syms)
    _print_group("1/3 -- NOVA (MonkeyBusiness RSI Cascade)", third_f, nova_weight, nova_syms)

    unaccounted = 1.0 - (ftl_weight + walters_weight + nova_weight)
    if abs(unaccounted) > 0.01:
        print(f"\n  {YELLOW}Unaccounted weight: {_pct(unaccounted)}{RESET}")


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
