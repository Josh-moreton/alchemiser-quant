#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Debug script for running a single strategy with full condition tracing.

This script runs a strategy locally with debug mode enabled, outputting
detailed traces of all condition evaluations to help diagnose signal
discrepancies with Composer.trade.

Usage:
    poetry run python scripts/debug_strategy.py simons_kmlm
    poetry run python scripts/debug_strategy.py chicken_rice
    poetry run python scripts/debug_strategy.py --list  # List all strategies

"""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

# Set environment variables for S3 market data access
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Add functions/strategy_worker to path for imports
strategy_worker_path = Path(__file__).parent.parent / "functions" / "strategy_worker"
sys.path.insert(0, str(strategy_worker_path))

# Add layers/shared to path for shared imports
shared_layer_path = Path(__file__).parent.parent / "layers" / "shared"
sys.path.insert(0, str(shared_layer_path))


def list_strategies() -> list[str]:
    """List all available strategy files.

    Returns:
        List of strategy file names (without .clj extension)

    """
    strategies_path = shared_layer_path / "the_alchemiser" / "shared" / "strategies"
    if not strategies_path.exists():
        print(f"Strategies path not found: {strategies_path}")
        return []

    strategies = []
    for f in strategies_path.glob("*.clj"):
        strategies.append(f.stem)
    return sorted(strategies)


def run_debug_strategy(strategy_name: str) -> dict:
    """Run a strategy with debug mode enabled.

    Args:
        strategy_name: Name of strategy (without .clj extension)

    Returns:
        Dictionary with results and debug traces

    """
    # Import after path setup
    from engines.dsl.engine import DslEngine

    from the_alchemiser.shared.data_v2.cached_market_data_adapter import (
        CachedMarketDataAdapter,
    )

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
    print(f"{'=' * 60}\n")

    # Read and print strategy content
    print("Strategy DSL:")
    print("-" * 40)
    print(full_path.read_text())
    print("-" * 40)
    print()

    # Create market data adapter with live bar injection enabled
    # This fetches current price from Alpaca and appends to historical data
    market_data_adapter = CachedMarketDataAdapter(append_live_bar=True)

    # Create DSL engine with debug mode
    engine = DslEngine(
        strategy_config_path=strategies_path,
        market_data_adapter=market_data_adapter,
        debug_mode=True,
    )

    # Evaluate strategy
    correlation_id = f"debug-{strategy_name}"
    allocation, trace = engine.evaluate_strategy(strategy_file, correlation_id)

    # Collect debug traces from evaluator
    debug_traces = engine.evaluator.debug_traces
    decision_path = engine.evaluator.decision_path

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print("\nTarget Allocation:")
    for symbol, weight in allocation.target_weights.items():
        print(f"  {symbol}: {weight:.4f}")

    print(f"\nTotal Weight: {sum(allocation.target_weights.values()):.4f}")

    if debug_traces:
        print("\n" + "=" * 60)
        print("DEBUG TRACES (Condition Evaluations)")
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

    if decision_path:
        print("\n" + "=" * 60)
        print("DECISION PATH")
        print("=" * 60)

        for i, decision in enumerate(decision_path, 1):
            condition = decision.get("condition", "?")
            result = decision.get("result", "?")
            branch = decision.get("branch", "?")
            values = decision.get("values", {})

            print(f"\n[{i}] {condition}")
            print(f"    Result: {result} -> Branch: {branch}")
            if values:
                print(f"    Values: {json.dumps(values, indent=8)}")

    return {
        "allocation": {k: float(v) for k, v in allocation.target_weights.items()},
        "debug_traces": debug_traces,
        "decision_path": decision_path,
    }


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Debug a strategy with full condition tracing"
    )
    parser.add_argument(
        "strategy",
        nargs="?",
        help="Strategy name (without .clj extension)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available strategies",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    if args.list:
        strategies = list_strategies()
        print("\nAvailable strategies:")
        for s in strategies:
            print(f"  - {s}")
        return

    if not args.strategy:
        parser.print_help()
        print("\n\nExample: poetry run python scripts/debug_strategy.py simons_kmlm")
        return

    try:
        result = run_debug_strategy(args.strategy)
        if args.json:
            print("\n" + json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nAvailable strategies:")
        for s in list_strategies():
            print(f"  - {s}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
