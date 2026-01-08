"""Trace the exact filter execution for ftl_starburst.

Business Unit: debugging | Status: development.
"""
import sys
sys.path.insert(0, "/Users/joshmoreton/GitHub/alchemiser-quant/layers/shared")
sys.path.insert(0, "/Users/joshmoreton/GitHub/alchemiser-quant/functions/strategy_worker")

from decimal import Decimal
from pathlib import Path

from engines.dsl.engine import DslEngine


def main() -> None:
    """Run the ftl_starburst strategy with full tracing."""
    strategy_path = Path(
        "/Users/joshmoreton/GitHub/alchemiser-quant/layers/shared/"
        "the_alchemiser/shared/strategies/ftl_starburst.clj"
    )
    
    print("=" * 70)
    print("FULL DSL EVALUATION TRACE")
    print("=" * 70)
    print()
    
    # Create engine with debug mode enabled
    engine = DslEngine(
        strategy_config_path=strategy_path.parent,
        debug_mode=True,  # Enable full tracing
    )
    
    try:
        allocation, trace = engine.evaluate_strategy(
            str(strategy_path),
            correlation_id="trace-debug-001",
        )
        print(f"✓ Evaluation complete")
        print()
        print("-" * 70)
        print("FINAL PORTFOLIO RESULT:")
        print("-" * 70)
        print()
        
        total = sum(allocation.target_weights.values())
        for sym, weight in sorted(allocation.target_weights.items(), key=lambda x: -x[1]):
            pct = float(weight / total * 100) if total > 0 else 0
            print(f"  {sym}: {pct:.2f}%")
        
        print()
        print("-" * 70)
        print("DECISION PATH:")
        print("-" * 70)
        print()
        
        decision_path = trace.metadata.get("decision_path", [])
        for idx, decision in enumerate(decision_path[:20]):  # First 20 decisions
            print(f"  {idx + 1}. {decision}")
        
        if len(decision_path) > 20:
            print(f"  ... and {len(decision_path) - 20} more decisions")
        
        print()
        print("-" * 70)
        print("FILTER TRACES:")
        print("-" * 70)
        
        filter_traces = trace.metadata.get("filter_traces", [])
        for idx, ft in enumerate(filter_traces[:10]):  # First 10 filters
            print(f"\nFilter {idx + 1}:")
            print(f"  Mode: {ft.get('mode')}")
            print(f"  Order: {ft.get('order')}")
            print(f"  Limit: {ft.get('limit')}")
            print(f"  Condition: {ft.get('condition')}")
            
            if 'scored_candidates' in ft:
                print(f"  Scored candidates (top 3):")
                for cand in ft.get('scored_candidates', [])[:3]:
                    print(f"    - {cand}")
            
            if 'selected_candidate_ids' in ft:
                selected = ft.get('selected_candidate_ids', [])
                print(f"  Selected: {selected[:3]}")
        
        if len(filter_traces) > 10:
            print(f"\n  ... and {len(filter_traces) - 10} more filter traces")
        
    except Exception as e:
        print(f"✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
