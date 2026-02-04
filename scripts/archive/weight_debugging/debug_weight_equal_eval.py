"""Debug weight-equal evaluation with filters.

Business Unit: debugging | Status: development.
"""
import sys
sys.path.insert(0, "/Users/joshmoreton/GitHub/alchemiser-quant/layers/shared")
sys.path.insert(0, "/Users/joshmoreton/GitHub/alchemiser-quant/functions/strategy_worker")

import os
os.environ["MARKET_DATA_BUCKET"] = "alchemiser-dev-market-data"

from decimal import Decimal
from pathlib import Path

from engines.dsl.sexpr_parser import SexprParser
from engines.dsl.engine import DslEngine


def main() -> None:
    """Debug weight-equal with multiple filter children."""
    # Test case with filters like FTL structure - using symbols we have data for
    test_dsl = """
    (defsymphony
     "Test Strategy"
     {:asset-class "EQUITIES", :rebalance-frequency :daily}
     (weight-equal
      [(filter
        (stdev-return {:window 10})
        (select-bottom 1)
        [(group "G1" [(asset "TQQQ" nil)])
         (group "G2" [(asset "SOXL" nil)])])
       (filter
        (stdev-return {:window 10})
        (select-bottom 1)
        [(group "G3" [(asset "TECL" nil)])
         (group "G4" [(asset "SPY" nil)])])
       (filter
        (stdev-return {:window 10})
        (select-bottom 1)
        [(group "G5" [(asset "QQQ" nil)])
         (group "G6" [(asset "IWM" nil)])])]))
    """
    
    # Write to temp file
    test_file = Path("/tmp/test_weight_equal.clj")
    test_file.write_text(test_dsl)
    
    engine = DslEngine(debug_mode=True)
    
    try:
        allocation, trace = engine.evaluate_strategy(str(test_file), "test-001")
        
        print("=" * 60)
        print("RESULT - Weight-equal of 3 filters:")
        print("=" * 60)
        
        total = sum(allocation.target_weights.values())
        for sym, weight in sorted(allocation.target_weights.items(), key=lambda x: -x[1]):
            pct = float(weight / total * 100) if total > 0 else 0
            print(f"  {sym}: {pct:.2f}%")
        
        print()
        print("Expected: 3 winners (one per filter), each ~33.33%")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
