#!/usr/bin/env python3
"""Debug bento_collection.clj evaluation.

Business Unit: Scripts | Status: current.

This script traces the final weight_equal call to understand how weights combine.
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
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
from decimal import Decimal
import traceback

original_weight_equal = portfolio_module.weight_equal
original_group = portfolio_module.group
original_weight_inverse_volatility = portfolio_module.weight_inverse_volatility

call_counter = [0]
group_counter = [0]
all_weight_equal_results = []
call_depth = [0]  # Track nesting depth
weight_equal_stack = []  # Stack of call numbers

# Track when BIL and DRV/LABU first appear together
bil_only_calls = []  # Calls with BIL 100%
drv_labu_calls = []  # Calls with DRV+LABU (no BIL)
combined_calls = []  # Calls with all three


def patched_weight_equal(args, context):
    """Patched weight_equal with logging."""
    call_counter[0] += 1
    call_num = call_counter[0]
    call_depth[0] += 1
    current_depth = call_depth[0]
    weight_equal_stack.append(call_num)
    
    result = original_weight_equal(args, context)
    
    weight_equal_stack.pop()
    call_depth[0] -= 1
    
    has_bil = "BIL" in result.weights
    has_drv = "DRV" in result.weights
    has_labu = "LABU" in result.weights
    
    # Track different patterns
    if has_bil and not has_drv and not has_labu:
        bil_only_calls.append({
            "call_num": call_num,
            "depth": current_depth,
            "weights": {k: float(v)*100 for k, v in result.weights.items()},
        })
    elif (has_drv or has_labu) and not has_bil:
        drv_labu_calls.append({
            "call_num": call_num,
            "depth": current_depth,
            "weights": {k: float(v)*100 for k, v in result.weights.items()},
        })
    
    # THE CRITICAL POINT: when all three appear together
    if has_bil and (has_drv or has_labu):
        parent_call = weight_equal_stack[-1] if weight_equal_stack else 0
        combined_calls.append({
            "call_num": call_num,
            "depth": current_depth,
            "parent_call": parent_call,
            "num_args": len(args),
            "weights": {k: float(v)*100 for k, v in result.weights.items()},
        })
        
        # Log all combination points with args info
        print(f"\n[COMBINED] Call #{call_num} depth={current_depth} parent=#{parent_call}")
        print(f"  Args: {len(args)}")
        
        # Evaluate args to see what they become (at depth 4 only)
        if current_depth == 4:
            print("  Evaluating args to see child fragments...")
            for i, arg in enumerate(args[:3]):
                print(f"    Arg {i}: node_type={arg.node_type}")
                # What does this arg evaluate to?
                child_val = context.evaluate_node(arg, context.correlation_id, context.trace)
                print(f"      -> Evaluates to: {type(child_val).__name__}")
                if isinstance(child_val, PortfolioFragment):
                    frag = child_val
                    weights = dict(frag.weights)
                    print(f"      -> PortfolioFragment with {len(weights)} symbols")
                    for sym, w in sorted(weights.items(), key=lambda x: -float(x[1]))[:3]:
                        print(f"         {sym}: {float(w)*100:.2f}%")
                elif isinstance(child_val, list):
                    # Recursively print list structure
                    def print_list(lst, indent=0):
                        prefix = " " * indent
                        for j, item in enumerate(lst[:5]):
                            if isinstance(item, PortfolioFragment):
                                print(f"{prefix}[{j}]: PortfolioFragment (source={item.source_step}) with {len(item.weights)} symbols")
                                for sym, w in sorted(item.weights.items(), key=lambda x: -float(x[1])):
                                    print(f"{prefix}     {sym}: {float(w)*100:.4f}%")
                            elif isinstance(item, list):
                                print(f"{prefix}[{j}]: list with {len(item)} items")
                                print_list(item, indent + 5)
                            else:
                                print(f"{prefix}[{j}]: {type(item).__name__}")
                    
                    print(f"      -> List with {len(child_val)} items")
                    print_list(child_val, 9)
        
        for sym, w in sorted(result.weights.items(), key=lambda x: -float(x[1])):
            print(f"  {sym}: {float(w)*100:.4f}%")
    
    return result


def patched_group(args, context):
    """Patched group with logging."""
    group_counter[0] += 1
    group_num = group_counter[0]
    
    # Get group name
    name_node = args[0] if args else None
    name = context.evaluate_node(name_node, context.correlation_id, context.trace) if name_node else "unnamed"
    
    result = original_group(args, context)
    
    # Log group results that involve our target symbols
    if isinstance(result, PortfolioFragment):
        has_bil = "BIL" in result.weights
        has_drv = "DRV" in result.weights
        has_labu = "LABU" in result.weights
        
        if has_bil or has_drv or has_labu:
            print(f"\nGROUP #{group_num} '{name[:40]}...' -> {len(result.weights)} symbols")
            weights = sorted(result.weights.items(), key=lambda x: -float(x[1]))
            for sym, w in weights[:3]:
                print(f"  {sym}: {float(w)*100:.2f}%")
    
    return result


def patched_weight_inverse_volatility(args, context):
    """Patched weight_inverse_volatility with logging."""
    # Log the actual volatilities being used
    from engines.dsl.operators.portfolio import _extract_window, _collect_assets_from_args, _get_volatility_for_asset
    
    window = _extract_window(args, context)
    assets = _collect_assets_from_args(args[1:], context)
    
    print(f"\n[weight-inverse-volatility] window={window}, assets={assets}")
    for asset in assets:
        vol = _get_volatility_for_asset(asset, window, context)
        if vol:
            print(f"  {asset}: volatility={vol:.6f}, inverse={1/vol:.2f}")
    
    result = original_weight_inverse_volatility(args, context)
    
    # Check if this involves our target symbols
    has_bil = "BIL" in result.weights
    has_drv = "DRV" in result.weights
    has_labu = "LABU" in result.weights
    
    if has_bil or has_drv or has_labu:
        print(f"  Result weights:")
        for sym, w in sorted(result.weights.items(), key=lambda x: -float(x[1])):
            print(f"    {sym}: {float(w)*100:.4f}%")
    
    return result


portfolio_module.weight_equal = patched_weight_equal
portfolio_module.group = patched_group
portfolio_module.weight_inverse_volatility = patched_weight_inverse_volatility


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
    print("FINAL RESULT:")
    print("=" * 60)
    
    # Handle tuple result (allocation, trace)
    if isinstance(result, tuple):
        allocation = result[0]
        trace = result[1] if len(result) > 1 else None
    else:
        allocation = result
        trace = None
    
    if hasattr(allocation, 'target_weights'):
        weights = allocation.target_weights
    elif hasattr(allocation, 'weights'):
        weights = allocation.weights
    else:
        print(f"Result type: {type(allocation)}")
        print(f"Result: {allocation}")
        return
    
    # Sort by weight descending
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\nTotal positions: {len(weights)}")
    print(f"Total weight: {sum(float(w) for w in weights.values()):.4f}")
    
    print("\nAllocations:")
    for sym, w in sorted_weights:
        print(f"  {sym:8s}  {float(w)*100:7.2f}%")
    
    # Show decision path
    if hasattr(evaluator, 'decision_path') and evaluator.decision_path:
        print("\n" + "=" * 60)
        print("DECISION PATH:")
        print("=" * 60)
        for i, decision in enumerate(evaluator.decision_path[:10]):
            print(f"\n[{i+1}] {decision.get('condition', 'unknown')}")
            print(f"    Branch: {decision.get('branch', 'unknown')}")
    
    print(f"\nTotal weight_equal calls: {call_counter[0]}")
    print(f"Total group calls: {group_counter[0]}")
    
    # Summary of tracked calls
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"BIL-only calls: {len(bil_only_calls)}")
    print(f"DRV/LABU-only calls: {len(drv_labu_calls)}")
    print(f"Combined (BIL + DRV/LABU) calls: {len(combined_calls)}")
    
    if combined_calls:
        print("\nFirst combination point details:")
        first = combined_calls[0]
        print(f"  Call #{first['call_num']} with {first['num_args']} args")
        for sym, w in sorted(first['weights'].items(), key=lambda x: -x[1]):
            print(f"    {sym}: {w:.4f}%")


if __name__ == "__main__":
    main()
