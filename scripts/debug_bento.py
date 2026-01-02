#!/usr/bin/env python3
"""Debug bento_collection.clj evaluation.

Business Unit: Scripts | Status: current.

This script traces the DSL evaluation of bento_collection to understand 
why weights are being calculated incorrectly.
"""

import sys
import os

# Add function paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions", "data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "layers", "shared"))

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Set bucket
os.environ["MARKET_DATA_BUCKET"] = "alchemiser-dev-market-data"

from the_alchemiser.shared.logging import configure_application_logging, get_logger
configure_application_logging()
logger = get_logger(__name__)

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from engines.dsl.dsl_evaluator import DslEvaluator
from engines.dsl.sexpr_parser import SexprParser
from indicators.indicator_service import IndicatorService

# Patch weight_equal to add logging
import engines.dsl.operators.portfolio as portfolio_module
from decimal import Decimal

original_weight_equal = portfolio_module.weight_equal
original_collect_weights = portfolio_module.collect_weights_from_value

weight_equal_calls = []
collect_weights_details = []

def patched_collect_weights(value):
    """Patched collect_weights_from_value with logging."""
    result = original_collect_weights(value)
    
    # Log interesting calls
    interesting = {"BIL", "DRV", "LABU"}
    if any(sym in result for sym in interesting):
        collect_weights_details.append({
            "value_type": type(value).__name__,
            "result": dict(result),
            "value_len": len(value) if isinstance(value, list) else 1
        })
    
    return result

portfolio_module.collect_weights_from_value = patched_collect_weights

def patched_weight_equal(args, context):
    """Patched weight_equal with logging."""
    # Capture pre-evaluation state
    pre_weights = []
    for arg in args:
        result = context.evaluate_node(arg, context.correlation_id, context.trace)
        arg_weights = original_collect_weights(result)
        pre_weights.append(arg_weights)
    
    # Now get the actual result (this re-evaluates, but memoization should handle it)
    result = original_weight_equal(args, context)
    
    # Log key weight_equal calls that have BIL, DRV, or LABU
    interesting = {"BIL", "DRV", "LABU"}
    if any(sym in result.weights for sym in interesting):
        weight_equal_calls.append({
            "num_args": len(args),
            "weights": dict(result.weights),
            "pre_weights": pre_weights
        })
    
    return result

portfolio_module.weight_equal = patched_weight_equal


def main():
    """Evaluate bento_collection and show the weights."""
    strategy_file = Path(__file__).parent.parent / "layers" / "shared" / "the_alchemiser" / "shared" / "strategies" / "bento_collection.clj"
    
    print(f"Reading: {strategy_file}")
    dsl_code = strategy_file.read_text()
    
    print(f"Strategy length: {len(dsl_code)} chars, {len(dsl_code.splitlines())} lines")
    
    # Parse DSL
    parser = SexprParser()
    ast = parser.parse(dsl_code)
    
    # Create services
    store = MarketDataStore()
    adapter = CachedMarketDataAdapter(market_data_store=store)
    indicator_service = IndicatorService(market_data_service=adapter)
    
    # Evaluate
    evaluator = DslEvaluator(indicator_service=indicator_service)
    
    print("\nEvaluating strategy...")
    result = evaluator.evaluate(ast, correlation_id="debug-bento")
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    
    # Handle tuple result (allocation, trace)
    allocation = result[0] if isinstance(result, tuple) else result
    trace = result[1] if isinstance(result, tuple) and len(result) > 1 else None
    
    if hasattr(allocation, 'target_weights'):
        weights = allocation.target_weights
        # Sort by weight descending
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\nTotal positions: {len(weights)}")
        print(f"Total weight: {sum(float(w) for w in weights.values()):.4f}")
        
        print("\nAllocations:")
        for sym, w in sorted_weights:
            print(f"  {sym:8s}  {float(w)*100:7.2f}%")
    elif hasattr(allocation, 'weights'):
        weights = allocation.weights
        # Sort by weight descending
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\nTotal positions: {len(weights)}")
        print(f"Total weight: {sum(float(w) for w in weights.values()):.4f}")
        
        print("\nAllocations:")
        for sym, w in sorted_weights:
            print(f"  {sym:8s}  {float(w)*100:7.2f}%")
    else:
        print(f"Result type: {type(allocation)}")
        print(f"Result: {allocation}")
    
    # Print weight_equal call statistics
    print("\n" + "=" * 60)
    print("WEIGHT-EQUAL CALL ANALYSIS:")
    print("=" * 60)
    
    print(f"\nTotal calls with BIL/DRV/LABU: {len(weight_equal_calls)}")
    
    # Count calls by number of arguments
    args_counts = {}
    for call in weight_equal_calls:
        n = call["num_args"]
        args_counts[n] = args_counts.get(n, 0) + 1
    
    print("\nCalls by number of arguments:")
    for n in sorted(args_counts.keys()):
        print(f"  {n} args: {args_counts[n]} calls")
    
    # Show last few calls (most likely the aggregation)
    print("\nLast 5 weight_equal calls (most aggregated):")
    for i, call in enumerate(weight_equal_calls[-5:]):
        idx = len(weight_equal_calls) - 4 + i
        print(f"\n  Call {idx}:")
        print(f"    num_args: {call['num_args']}")
        print(f"    pre_weights: {call['pre_weights']}")
        weights = call['weights']
        for sym, w in sorted(weights.items(), key=lambda x: -float(x[1])):
            if float(w) > 0.001:
                print(f"    Output {sym}: {float(w)*100:.2f}%")
    
    # Show collect_weights statistics
    print("\n" + "=" * 60)
    print("COLLECT_WEIGHTS ANALYSIS:")
    print("=" * 60)
    
    # Count by type
    type_counts = {}
    for call in collect_weights_details:
        t = call["value_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print(f"\nTotal calls: {len(collect_weights_details)}")
    print("\nCalls by value type:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")
    
    # Look for calls with multiple items
    multi_item = [c for c in collect_weights_details if c["value_len"] > 1]
    print(f"\nCalls with multiple items: {len(multi_item)}")
    if multi_item:
        print("\nFirst 5 multi-item calls:")
        for c in multi_item[:5]:
            print(f"  Type: {c['value_type']}, Len: {c['value_len']}, Result: {c['result']}")


if __name__ == "__main__":
    main()
