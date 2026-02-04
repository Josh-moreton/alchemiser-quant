"""Business Unit: Strategy | Status: current.

Indicator Matrix Test - Tests individual indicator live bar settings.
Tests RSI, cumulative_return, and moving_average with T0 (live) vs T1 (non-live).
"""

import json
import subprocess
import sys
from pathlib import Path


def run_trace(strategy: str, indicator_config: dict[str, bool]) -> dict[str, float]:
    """Run trace_strategy_routes with custom indicator config."""
    config_json = json.dumps(indicator_config)
    out_file = Path("/tmp/indicator_test_out.json")
    
    cmd = [
        "poetry", "run", "python", "scripts/trace_strategy_routes.py",
        strategy,
        "--policy", "custom",
        "--indicator-config", config_json,
        "--out", str(out_file)
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    if result.returncode != 0:
        print(f"ERROR running {strategy}: {result.stderr}", file=sys.stderr)
        return {}
    
    try:
        with open(out_file) as f:
            data = json.load(f)
        return data.get("allocation", {})
    except Exception as e:
        print(f"ERROR parsing output for {strategy}: {e}", file=sys.stderr)
        return {}


def format_allocation(alloc: dict[str, float]) -> str:
    """Format allocation as a readable string."""
    if not alloc:
        return "ERROR"
    sorted_items = sorted(
        [(s, w) for s, w in alloc.items() if w > 0.001],
        key=lambda x: (-x[1], x[0])
    )
    return " + ".join(f"{s}:{w*100:.0f}%" for s, w in sorted_items)


def main() -> None:
    """Run indicator matrix tests."""
    strategies = [
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
    
    # Test configurations: (name, config)
    indicator_tests = [
        ("RSI=T0 (live)", {"rsi": True}),
        ("RSI=T1 (off)", {"rsi": False}),
        ("cumret=T0 (live)", {"cumulative_return": True}),
        ("cumret=T1 (off)", {"cumulative_return": False}),
        ("MA=T0 (live)", {"moving_average": True}),
        ("MA=T1 (off)", {"moving_average": False}),
        ("ALL=T1 (none-live)", {"rsi": False, "cumulative_return": False, "moving_average": False}),
    ]
    
    print("=" * 80)
    print("INDICATOR MATRIX TEST - Individual indicator live bar impact")
    print("=" * 80)
    print()
    
    for strategy in strategies:
        print(f"\n{'='*60}")
        print(f"Strategy: {strategy}")
        print("=" * 60)
        
        results = {}
        for test_name, config in indicator_tests:
            alloc = run_trace(strategy, config)
            alloc_str = format_allocation(alloc)
            results[test_name] = alloc_str
            print(f"  {test_name:25s}: {alloc_str}")
        
        # Identify differences
        print()
        print("  --- Analysis ---")
        
        # RSI impact
        if results.get("RSI=T0 (live)") != results.get("RSI=T1 (off)"):
            print("  ⚠️  RSI live bar CHANGES allocation!")
        else:
            print("  ✓  RSI live bar has no impact")
        
        # Cumret impact
        if results.get("cumret=T0 (live)") != results.get("cumret=T1 (off)"):
            print("  ⚠️  cumulative_return live bar CHANGES allocation!")
        else:
            print("  ✓  cumulative_return live bar has no impact")
        
        # MA impact
        if results.get("MA=T0 (live)") != results.get("MA=T1 (off)"):
            print("  ⚠️  moving_average live bar CHANGES allocation!")
        else:
            print("  ✓  moving_average live bar has no impact")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
