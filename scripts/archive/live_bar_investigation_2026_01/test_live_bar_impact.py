#!/usr/bin/env python3
"""Business Unit: Scripts | Status: current.

Comprehensive test script to analyze live bar vs non-live bar impact on ALL strategies.

This script runs each of the 12 strategies with three policies:
  1. all-live: All indicators use today's partial bar
  2. none-live: All indicators use T-1 completed bars only
  3. composer: Per-indicator config (mirrors Composer's expected behavior)

For each strategy, it reports:
  - Final allocation under each policy
  - Whether allocations differ between policies
  - Which RSI comparisons are near decision thresholds (within 5 points)
  - Key RSI values that change between live/non-live

Usage:
    poetry run python scripts/test_live_bar_impact.py
    poetry run python scripts/test_live_bar_impact.py --strategy blatant_tech  # Single strategy
    poetry run python scripts/test_live_bar_impact.py --json  # JSON output
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))
sys.path.insert(0, str(PROJECT_ROOT / "functions" / "strategy_worker"))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# All 12 strategies
ALL_STRATEGIES = [
    "blatant_tech",
    "defence",
    "gold",
    "nuclear",
    "pals_spell",
    "rains_concise_em",
    "rains_em_dancer",
    "simons_full_kmlm",
    "sisyphus_lowvol",
    "tqqq_ftlt",
    "tqqq_ftlt_1",
    "tqqq_ftlt_2",
]

# RSI windows used per strategy (from analysis)
RSI_WINDOWS_BY_STRATEGY = {
    "blatant_tech": [3, 7, 9, 10, 30, 32],
    "defence": [7, 10],
    "gold": [2, 10, 14, 20],
    "nuclear": [10],
    "pals_spell": [10],
    "rains_concise_em": [6, 10, 14, 15],
    "rains_em_dancer": [6, 10, 12, 14, 15],
    "simons_full_kmlm": [10],
    "sisyphus_lowvol": [10, 20, 21, 60],
    "tqqq_ftlt": [10],
    "tqqq_ftlt_1": [9, 10, 14],
    "tqqq_ftlt_2": [10, 15, 20, 60],
}


@dataclass
class RSIComparison:
    """A single RSI comparison from the decision path."""

    left_symbol: str
    left_window: int
    left_value: float
    right_symbol: str | None  # None if comparing to threshold
    right_window: int | None
    right_value: float
    operator: str
    result: bool
    diff: float  # How close to decision threshold

    @property
    def is_near_threshold(self) -> bool:
        """Check if this comparison is within 5 points of flipping."""
        return abs(self.diff) < 5.0

    @property
    def description(self) -> str:
        """Human-readable description."""
        if self.right_symbol:
            return (
                f"{self.left_symbol} RSI({self.left_window})={self.left_value:.2f} "
                f"{self.operator} {self.right_symbol} RSI({self.right_window})={self.right_value:.2f} "
                f"-> {self.result} (diff: {self.diff:+.2f})"
            )
        return (
            f"{self.left_symbol} RSI({self.left_window})={self.left_value:.2f} "
            f"{self.operator} {self.right_value:.0f} -> {self.result} (diff: {self.diff:+.2f})"
        )


@dataclass
class StrategyResult:
    """Result of running a strategy with a specific policy."""

    strategy: str
    policy: str
    allocation: dict[str, float]
    decision_path: list[dict]
    debug_traces: list[dict]
    rsi_comparisons: list[RSIComparison] = field(default_factory=list)
    error: str | None = None


@dataclass
class StrategyAnalysis:
    """Complete analysis of a strategy across all policies."""

    strategy: str
    all_live: StrategyResult | None
    none_live: StrategyResult | None
    composer: StrategyResult | None
    allocations_match: bool = False
    critical_rsi_comparisons: list[RSIComparison] = field(default_factory=list)
    recommendation: str = ""


def run_trace(strategy: str, policy: str) -> StrategyResult:
    """Run trace_strategy_routes.py for a strategy with given policy."""
    output_file = f"/tmp/trace_{strategy}_{policy}.json"
    cmd = [
        "poetry",
        "run",
        "python",
        str(PROJECT_ROOT / "scripts" / "trace_strategy_routes.py"),
        strategy,
        "--policy",
        policy,
        "--out",
        output_file,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )

        if result.returncode != 0:
            return StrategyResult(
                strategy=strategy,
                policy=policy,
                allocation={},
                decision_path=[],
                debug_traces=[],
                error=f"Trace failed: {result.stderr[:500]}",
            )

        # Read the output file
        with open(output_file) as f:
            data = json.load(f)

        # Parse RSI comparisons from debug_traces
        rsi_comparisons = parse_rsi_comparisons(data.get("debug_traces", []))

        return StrategyResult(
            strategy=strategy,
            policy=policy,
            allocation=data.get("allocation", {}),
            decision_path=data.get("decision_path", []),
            debug_traces=data.get("debug_traces", []),
            rsi_comparisons=rsi_comparisons,
        )

    except subprocess.TimeoutExpired:
        return StrategyResult(
            strategy=strategy,
            policy=policy,
            allocation={},
            decision_path=[],
            debug_traces=[],
            error="Timeout after 120s",
        )
    except Exception as e:
        return StrategyResult(
            strategy=strategy,
            policy=policy,
            allocation={},
            decision_path=[],
            debug_traces=[],
            error=str(e),
        )


def parse_rsi_comparisons(debug_traces: list[dict]) -> list[RSIComparison]:
    """Extract RSI comparisons from debug traces."""
    comparisons = []

    for trace in debug_traces:
        # Check if this is an RSI-related comparison
        left_expr = trace.get("left_expr", "")
        if "rsi" not in left_expr.lower():
            continue

        left_value = trace.get("left_value")
        right_value = trace.get("right_value")
        right_expr = trace.get("right_expr", "")
        operator = trace.get("operator", ">")
        result = trace.get("result", False)

        if left_value is None or right_value is None:
            continue

        # Parse left side - "rsi(SYMBOL)"
        left_symbol = extract_symbol(left_expr)
        left_window = 10  # Default, try to extract from trace

        # Check if right side is RSI or threshold
        if "rsi" in right_expr.lower():
            right_symbol = extract_symbol(right_expr)
            right_window = 10
            diff = left_value - right_value
        else:
            right_symbol = None
            right_window = None
            if operator in (">", ">="):
                diff = left_value - right_value
            else:
                diff = right_value - left_value

        comparisons.append(
            RSIComparison(
                left_symbol=left_symbol,
                left_window=left_window,
                left_value=left_value,
                right_symbol=right_symbol,
                right_window=right_window,
                right_value=right_value,
                operator=operator,
                result=result,
                diff=diff,
            )
        )

    return comparisons


def extract_symbol(expr: str) -> str:
    """Extract symbol from expression like 'rsi(SYMBOL)'."""
    if "(" in expr and ")" in expr:
        start = expr.find("(") + 1
        end = expr.find(")")
        return expr[start:end]
    return expr


def analyze_strategy(strategy: str) -> StrategyAnalysis:
    """Run a strategy with all three policies and analyze differences."""
    print(f"\n{'='*60}")
    print(f"Testing: {strategy}")
    print(f"RSI windows used: {RSI_WINDOWS_BY_STRATEGY.get(strategy, [])}")
    print(f"{'='*60}")

    # Run with all three policies
    print("  Running with policy: all-live...", end=" ", flush=True)
    all_live = run_trace(strategy, "all-live")
    print("✓" if not all_live.error else f"✗ {all_live.error[:50]}")

    print("  Running with policy: none-live...", end=" ", flush=True)
    none_live = run_trace(strategy, "none-live")
    print("✓" if not none_live.error else f"✗ {none_live.error[:50]}")

    print("  Running with policy: composer...", end=" ", flush=True)
    composer = run_trace(strategy, "composer")
    print("✓" if not composer.error else f"✗ {composer.error[:50]}")

    # Check if allocations match
    allocations_match = (
        all_live.allocation == none_live.allocation == composer.allocation
    )

    # Find critical RSI comparisons (near thresholds)
    critical = []
    for result in [all_live, none_live, composer]:
        for comp in result.rsi_comparisons:
            if comp.is_near_threshold and comp not in critical:
                critical.append(comp)

    # Generate recommendation
    if allocations_match:
        recommendation = "✅ STABLE - Live bar has no impact on final allocation"
    elif all_live.allocation == composer.allocation and none_live.allocation != composer.allocation:
        recommendation = "⚠️ LIVE-DEPENDENT - Uses live bar, would differ with T-1 data"
    elif none_live.allocation == composer.allocation and all_live.allocation != composer.allocation:
        recommendation = "🔄 T-1-DEPENDENT - Current composer config matches T-1, live bar breaks it"
    else:
        recommendation = "❌ INCONSISTENT - All three policies give different results"

    return StrategyAnalysis(
        strategy=strategy,
        all_live=all_live,
        none_live=none_live,
        composer=composer,
        allocations_match=allocations_match,
        critical_rsi_comparisons=critical,
        recommendation=recommendation,
    )


def format_allocation(alloc: dict[str, float]) -> str:
    """Format allocation as string."""
    if not alloc:
        return "(empty)"
    return " ".join(f"{k}:{v:.0%}" for k, v in sorted(alloc.items()))


def print_analysis(analysis: StrategyAnalysis) -> None:
    """Print detailed analysis for a strategy."""
    print(f"\n--- {analysis.strategy} ---")
    print(f"Recommendation: {analysis.recommendation}")
    print()

    # Allocations table
    print("Allocations:")
    if analysis.all_live:
        print(f"  all-live:  {format_allocation(analysis.all_live.allocation)}")
    if analysis.none_live:
        print(f"  none-live: {format_allocation(analysis.none_live.allocation)}")
    if analysis.composer:
        print(f"  composer:  {format_allocation(analysis.composer.allocation)}")

    # Show critical RSI comparisons
    if analysis.critical_rsi_comparisons:
        print("\nCritical RSI comparisons (within 5 points of flipping):")
        for comp in analysis.critical_rsi_comparisons[:5]:  # Limit to 5
            print(f"  {comp.description}")

    # Show RSI values that changed between live and non-live
    if analysis.all_live and analysis.none_live:
        changed_rsi = find_changed_rsi(
            analysis.all_live.debug_traces, analysis.none_live.debug_traces
        )
        if changed_rsi:
            print("\nRSI values that changed with live bar:")
            for symbol, (live_val, t1_val, window) in list(changed_rsi.items())[:5]:
                change = live_val - t1_val
                print(
                    f"  {symbol} RSI({window}): {t1_val:.2f} → {live_val:.2f} (Δ{change:+.2f})"
                )


def find_changed_rsi(
    live_traces: list[dict], t1_traces: list[dict]
) -> dict[str, tuple[float, float, int]]:
    """Find RSI values that differ between live and T-1 data."""
    live_rsi: dict[str, float] = {}
    t1_rsi: dict[str, float] = {}

    for trace in live_traces:
        left_expr = trace.get("left_expr", "")
        if "rsi" in left_expr.lower():
            symbol = extract_symbol(left_expr)
            live_rsi[symbol] = trace.get("left_value", 0)

    for trace in t1_traces:
        left_expr = trace.get("left_expr", "")
        if "rsi" in left_expr.lower():
            symbol = extract_symbol(left_expr)
            t1_rsi[symbol] = trace.get("left_value", 0)

    changed = {}
    for symbol in live_rsi:
        if symbol in t1_rsi:
            if abs(live_rsi[symbol] - t1_rsi[symbol]) > 0.5:  # More than 0.5 change
                changed[symbol] = (live_rsi[symbol], t1_rsi[symbol], 10)

    return changed


def print_summary(analyses: list[StrategyAnalysis]) -> None:
    """Print summary table of all strategies."""
    print("\n" + "=" * 80)
    print("SUMMARY: Live Bar Impact on RSI Calculations")
    print("=" * 80)
    print(f"\nTest Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Summary table
    print(f"{'Strategy':<20} {'all-live':<30} {'none-live':<30} {'Match?':<8}")
    print("-" * 90)

    stable_count = 0
    for a in analyses:
        all_live_str = format_allocation(a.all_live.allocation if a.all_live else {})[:28]
        none_live_str = format_allocation(a.none_live.allocation if a.none_live else {})[:28]
        match = "✅" if a.allocations_match else "❌"
        if a.allocations_match:
            stable_count += 1
        print(f"{a.strategy:<20} {all_live_str:<30} {none_live_str:<30} {match:<8}")

    print("-" * 90)
    print(f"\nStrategies unaffected by live bar: {stable_count}/{len(analyses)}")

    # Group by recommendation
    print("\n" + "-" * 40)
    print("RECOMMENDATIONS:")
    print("-" * 40)
    for a in analyses:
        print(f"  {a.strategy}: {a.recommendation}")

    # Critical findings
    print("\n" + "-" * 40)
    print("CRITICAL RSI COMPARISONS (near decision thresholds):")
    print("-" * 40)
    for a in analyses:
        if a.critical_rsi_comparisons:
            print(f"\n  {a.strategy}:")
            for comp in a.critical_rsi_comparisons[:3]:
                print(f"    • {comp.description}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test live bar vs non-live bar impact on all strategies"
    )
    parser.add_argument(
        "--strategy",
        "-s",
        help="Test only this strategy (default: all 12)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    strategies = [args.strategy] if args.strategy else ALL_STRATEGIES

    print("=" * 80)
    print("LIVE BAR vs NON-LIVE BAR RSI IMPACT ANALYSIS")
    print("=" * 80)
    print(f"Testing {len(strategies)} strategies...")
    print(f"Policies: all-live, none-live, composer")

    analyses = []
    for strategy in strategies:
        analysis = analyze_strategy(strategy)
        analyses.append(analysis)
        print_analysis(analysis)

    if args.json:
        # Output as JSON
        output = {
            "test_date": datetime.now(timezone.utc).isoformat(),
            "strategies": [
                {
                    "name": a.strategy,
                    "allocations_match": a.allocations_match,
                    "recommendation": a.recommendation,
                    "all_live": a.all_live.allocation if a.all_live else {},
                    "none_live": a.none_live.allocation if a.none_live else {},
                    "composer": a.composer.allocation if a.composer else {},
                }
                for a in analyses
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print_summary(analyses)


if __name__ == "__main__":
    main()
