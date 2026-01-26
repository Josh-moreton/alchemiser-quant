#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Compare T-0 (all-live) vs T-1 (none-live) signal divergence for failing strategies.

Runs each strategy with both policies and shows:
- Allocation differences
- Key indicator values that drove the decision
- Which branch of if-statements was taken

Usage:
    poetry run python scripts/compare_live_bar_impact.py

    # Single strategy
    poetry run python scripts/compare_live_bar_impact.py --strategy rains_concise_em

    # Custom indicator config comparison
    poetry run python scripts/compare_live_bar_impact.py --strategy blatant_tech --rsi-live --cumret-off

"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "functions" / "strategy_worker"))
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))

os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from dotenv import load_dotenv

load_dotenv()

# Import after path setup
from scripts.trace_strategy_routes import (
    Policy,
    RunConfig,
    run_trace,
    set_indicator_overrides,
    _apply_live_bar_policy,
)

# Failing strategies from 2026-01-15 validation
FAILING_STRATEGIES = [
    ("blatant_tech", "CORD NBIS SOX", "Uses RSI on GDX to decide Metals group"),
    ("rains_concise_em", "EDZ XLF", "Nested RSI comparisons for Leveraged Sectors"),
    ("rains_em_dancer", "EDZ (correct weight)", "Uses cumulative_return for filter"),
    ("sisyphus_lowvol", "Unknown", "Uses cumulative_return extensively"),
]


@dataclass
class ComparisonResult:
    strategy: str
    expected: str
    all_live_allocation: dict[str, float]
    none_live_allocation: dict[str, float]
    all_live_symbols: set[str]
    none_live_symbols: set[str]
    symbols_only_in_all_live: set[str]
    symbols_only_in_none_live: set[str]
    decision_path_all_live: list[str]
    decision_path_none_live: list[str]
    debug_traces_all_live: list[dict]
    debug_traces_none_live: list[dict]


def run_comparison(strategy_name: str, expected: str) -> ComparisonResult:
    """Run strategy with all-live and none-live, compare results."""

    # Run with all-live (T-0)
    cfg_all = RunConfig(
        strategy_name=strategy_name,
        mode="live",
        policy="all-live",
        append_live_bar=True,
        as_of=None,
    )
    result_all = run_trace(cfg_all)

    # Run with none-live (T-1)
    cfg_none = RunConfig(
        strategy_name=strategy_name,
        mode="live",
        policy="none-live",
        append_live_bar=True,
        as_of=None,
    )
    result_none = run_trace(cfg_none)

    alloc_all = result_all["allocation"]
    alloc_none = result_none["allocation"]

    symbols_all = {s for s, w in alloc_all.items() if w > 0.001}
    symbols_none = {s for s, w in alloc_none.items() if w > 0.001}

    return ComparisonResult(
        strategy=strategy_name,
        expected=expected,
        all_live_allocation=alloc_all,
        none_live_allocation=alloc_none,
        all_live_symbols=symbols_all,
        none_live_symbols=symbols_none,
        symbols_only_in_all_live=symbols_all - symbols_none,
        symbols_only_in_none_live=symbols_none - symbols_all,
        decision_path_all_live=result_all.get("decision_path", []),
        decision_path_none_live=result_none.get("decision_path", []),
        debug_traces_all_live=result_all.get("debug_traces", []),
        debug_traces_none_live=result_none.get("debug_traces", []),
    )


def find_divergent_comparisons(
    traces_all: list[dict], traces_none: list[dict]
) -> list[dict]:
    """Find debug traces where the result differs between all-live and none-live."""
    divergent = []

    # Build lookup by description
    all_by_desc = {t.get("description", ""): t for t in traces_all}
    none_by_desc = {t.get("description", ""): t for t in traces_none}

    for desc, t_all in all_by_desc.items():
        t_none = none_by_desc.get(desc)
        if t_none and t_all.get("result") != t_none.get("result"):
            divergent.append({
                "description": desc,
                "all_live": {
                    "left": t_all.get("left"),
                    "right": t_all.get("right"),
                    "result": t_all.get("result"),
                },
                "none_live": {
                    "left": t_none.get("left"),
                    "right": t_none.get("right"),
                    "result": t_none.get("result"),
                },
            })

    return divergent


def format_allocation(alloc: dict[str, float]) -> str:
    """Format allocation as compact string."""
    items = [(s, w) for s, w in sorted(alloc.items()) if w > 0.001]
    return " + ".join(f"{s}:{w*100:.0f}%" for s, w in items)


def print_comparison(result: ComparisonResult) -> None:
    """Print comparison results."""
    print("\n" + "=" * 80)
    print(f"STRATEGY: {result.strategy}")
    print(f"Expected (Composer): {result.expected}")
    print("=" * 80)

    print(f"\n📊 ALL-LIVE (T-0):  {format_allocation(result.all_live_allocation)}")
    print(f"📊 NONE-LIVE (T-1): {format_allocation(result.none_live_allocation)}")

    if result.all_live_symbols == result.none_live_symbols:
        print("\n✅ Same symbols selected")
        # Check weight differences
        weight_diffs = []
        for s in result.all_live_symbols:
            w_all = result.all_live_allocation.get(s, 0)
            w_none = result.none_live_allocation.get(s, 0)
            if abs(w_all - w_none) > 0.01:
                weight_diffs.append((s, w_all, w_none))
        if weight_diffs:
            print("   ⚠️  Weight differences:")
            for s, w_all, w_none in weight_diffs:
                print(f"      {s}: {w_all*100:.1f}% (T-0) vs {w_none*100:.1f}% (T-1)")
    else:
        print("\n❌ DIFFERENT SYMBOLS:")
        if result.symbols_only_in_all_live:
            print(f"   Only in T-0 (all-live): {result.symbols_only_in_all_live}")
        if result.symbols_only_in_none_live:
            print(f"   Only in T-1 (none-live): {result.symbols_only_in_none_live}")

    # Find divergent comparisons (RSI, cumulative_return, etc.)
    divergent = find_divergent_comparisons(
        result.debug_traces_all_live, result.debug_traces_none_live
    )
    if divergent:
        print("\n🔍 DIVERGENT COMPARISONS (result flipped between T-0 and T-1):")
        for d in divergent[:10]:  # Show first 10
            print(f"\n   {d['description']}")
            print(f"      T-0: {d['all_live']['left']:.4f} vs {d['all_live']['right']:.4f} → {d['all_live']['result']}")
            print(f"      T-1: {d['none_live']['left']:.4f} vs {d['none_live']['right']:.4f} → {d['none_live']['result']}")

    # Show decision path differences
    if result.decision_path_all_live != result.decision_path_none_live:
        print("\n📍 DECISION PATH DIFFERS:")
        # Handle both string and dict decision paths
        def format_path(path):
            items = []
            for p in path[:5]:
                if isinstance(p, dict):
                    items.append(p.get("description", str(p))[:40])
                else:
                    items.append(str(p)[:40])
            return " → ".join(items)
        print(f"   T-0: {format_path(result.decision_path_all_live)}")
        print(f"   T-1: {format_path(result.decision_path_none_live)}")


def run_custom_config(
    strategy_name: str,
    rsi_live: bool,
    cumret_live: bool,
) -> dict[str, float]:
    """Run strategy with custom RSI and cumulative_return settings."""
    set_indicator_overrides({
        "rsi": rsi_live,
        "cumulative_return": cumret_live,
    })
    _apply_live_bar_policy("custom")

    cfg = RunConfig(
        strategy_name=strategy_name,
        mode="live",
        policy="custom",
        append_live_bar=True,
        as_of=None,
    )
    result = run_trace(cfg)
    return result["allocation"]


def print_config_matrix(strategy_name: str, expected: str) -> None:
    """Print 2x2 matrix of RSI x cumulative_return settings."""
    print(f"\n{'='*80}")
    print(f"CONFIG MATRIX: {strategy_name}")
    print(f"Expected: {expected}")
    print("="*80)
    print("\n                    | cumret=T-0 (live) | cumret=T-1 (off)")
    print("--------------------+-------------------+------------------")

    for rsi_live in [True, False]:
        row_label = f"RSI=T-0 (live)" if rsi_live else f"RSI=T-1 (off) "
        results = []
        for cumret_live in [True, False]:
            alloc = run_custom_config(strategy_name, rsi_live, cumret_live)
            symbols = sorted([s for s, w in alloc.items() if w > 0.001])
            results.append(" ".join(symbols) if symbols else "(empty)")

        print(f"{row_label} | {results[0]:<17} | {results[1]}")


def main():
    parser = argparse.ArgumentParser(description="Compare T-0 vs T-1 live bar impact")
    parser.add_argument("--strategy", help="Single strategy to analyze")
    parser.add_argument("--matrix", action="store_true", help="Show 2x2 RSI x cumret matrix")
    parser.add_argument("--all", action="store_true", help="Run all failing strategies")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    strategies = []
    if args.strategy:
        # Find expected from FAILING_STRATEGIES or use "Unknown"
        expected = "Unknown"
        for name, exp, _ in FAILING_STRATEGIES:
            if name == args.strategy:
                expected = exp
                break
        strategies = [(args.strategy, expected)]
    elif args.all:
        strategies = [(name, exp) for name, exp, _ in FAILING_STRATEGIES]
    else:
        strategies = [(name, exp) for name, exp, _ in FAILING_STRATEGIES]

    print("=" * 80)
    print("LIVE BAR IMPACT COMPARISON: T-0 (all-live) vs T-1 (none-live)")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    for strategy_name, expected in strategies:
        if args.matrix:
            print_config_matrix(strategy_name, expected)
        else:
            try:
                result = run_comparison(strategy_name, expected)
                if args.json:
                    print(json.dumps({
                        "strategy": result.strategy,
                        "expected": result.expected,
                        "all_live": result.all_live_allocation,
                        "none_live": result.none_live_allocation,
                        "symbols_diff": {
                            "only_in_all_live": list(result.symbols_only_in_all_live),
                            "only_in_none_live": list(result.symbols_only_in_none_live),
                        },
                    }, indent=2))
                else:
                    print_comparison(result)
            except Exception as e:
                print(f"\n❌ Error running {strategy_name}: {e}")
                import traceback
                traceback.print_exc()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nCurrent partial_bar_config.py settings:")
    from the_alchemiser.shared.indicators.partial_bar_config import get_all_indicator_configs
    for name, cfg in get_all_indicator_configs().items():
        status = "✅ T-0" if cfg.use_live_bar else "❌ T-1"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
