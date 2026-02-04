"""Trace _flatten_to_weight_dicts behavior.

Business Unit: debugging | Status: development.
"""
import sys
sys.path.insert(0, "/Users/joshmoreton/GitHub/alchemiser-quant/layers/shared")
sys.path.insert(0, "/Users/joshmoreton/GitHub/alchemiser-quant/functions/strategy_worker")

from decimal import Decimal
from pathlib import Path

from engines.dsl.operators import portfolio as p

# Save original function
original_flatten = p._flatten_to_weight_dicts

flatten_call_count = 0


def traced_flatten(items):
    """Wrapper that traces flatten calls."""
    global flatten_call_count
    flatten_call_count += 1
    
    item_type = type(items).__name__
    item_len = len(items) if isinstance(items, list) else 1
    
    # Only print first 10 and last 5 calls
    if flatten_call_count <= 10 or flatten_call_count > 180:
        print(f"[{flatten_call_count}] _flatten: type={item_type}, len={item_len}")
        if isinstance(items, list):
            for i, item in enumerate(items[:3]):  # First 3 items only
                weights = getattr(item, "weights", None)
                print(f"       Item {i}: {type(item).__name__}, weights={list(weights.keys())[:3] if weights else None}")
    
    result = original_flatten(items)
    
    if flatten_call_count <= 10 or flatten_call_count > 180:
        print(f"       Result: {len(result)} weight dicts")
    
    return result


# Patch the function
p._flatten_to_weight_dicts = traced_flatten

# Now import engine and run
from engines.dsl.engine import DslEngine


def main() -> None:
    """Run the ftl_starburst strategy with flatten tracing."""
    strategy_path = Path(
        "/Users/joshmoreton/GitHub/alchemiser-quant/layers/shared/"
        "the_alchemiser/shared/strategies/ftl_starburst.clj"
    )
    
    print("=" * 70)
    print("_FLATTEN_TO_WEIGHT_DICTS TRACE")
    print("=" * 70)
    print()
    
    engine = DslEngine(
        strategy_config_path=strategy_path.parent,
        debug_mode=True,
    )
    
    try:
        allocation, trace = engine.evaluate_strategy(
            str(strategy_path),
            correlation_id="flatten-trace-001",
        )
        print()
        print(f"Total _flatten calls: {flatten_call_count}")
        print()
        print("-" * 70)
        print("FINAL PORTFOLIO RESULT:")
        print("-" * 70)
        
        total = sum(allocation.target_weights.values())
        for sym, weight in sorted(allocation.target_weights.items(), key=lambda x: -x[1]):
            pct = float(weight / total * 100) if total > 0 else 0
            print(f"  {sym}: {pct:.2f}%")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
