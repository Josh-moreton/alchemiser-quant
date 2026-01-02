#!/usr/bin/env python3
"""Test ftl_starburst strategy with the filter fix.

Business Unit: Scripts | Status: current.
"""

import sys
import os

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(project_root, "layers", "shared"))

os.environ["MARKET_DATA_BUCKET"] = "alchemiser-dev-market-data"
os.environ.setdefault("AWS_REGION", "ap-southeast-2")

from the_alchemiser.shared.logging import configure_application_logging

configure_application_logging()

from engines.dsl.dsl_evaluator import DslEvaluator
from engines.dsl.sexpr_parser import SexprParser
from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from indicators.indicator_service import IndicatorService


def main() -> None:
    """Test ftl_starburst strategy evaluation."""
    # Load the strategy file
    strategy_path = os.path.join(
        project_root,
        "layers/shared/the_alchemiser/shared/strategies/ftl_starburst.clj",
    )
    with open(strategy_path) as f:
        strategy_content = f.read()

    print(f"Strategy loaded: {len(strategy_content)} chars")

    # Parse
    parser = SexprParser()
    ast = parser.parse(strategy_content)
    print("Strategy parsed successfully")

    # Set up evaluation context
    store = MarketDataStore()
    adapter = CachedMarketDataAdapter(market_data_store=store)
    indicator_service = IndicatorService(market_data_service=adapter)

    # Evaluate
    evaluator = DslEvaluator(indicator_service=indicator_service)
    result = evaluator.evaluate(ast, correlation_id="test-ftl")

    print("Strategy evaluated!")

    # Extract weights from result - handle various result types
    weights = {}
    if hasattr(result, "weights"):
        weights = result.weights
    elif isinstance(result, tuple):
        print(f"Result is tuple with {len(result)} elements")
        for i, elem in enumerate(result):
            print(f"  Element {i}: {type(elem)}")
            if hasattr(elem, "weights"):
                print(f"    Has weights: {dict(elem.weights)}")
                if not weights:
                    weights = elem.weights
            elif hasattr(elem, "target_weights"):
                print(f"    Has target_weights: {dict(elem.target_weights)}")
                if not weights:
                    weights = elem.target_weights
    else:
        print(f"Unexpected result type: {type(result)}")

    print("\nWeights:")
    for sym, w in sorted(weights.items(), key=lambda x: -float(x[1])):
        print(f"  {sym}: {float(w) * 100:.2f}%")

    print("\n" + "=" * 60)
    print("Expected (from Composer):")
    print("  COST 8%, EDC 22%, GE 4%, LLY 8%, NVO 2.5%, TECS 22%, TQQQ 33%")
    print("\nActual (before fix):")
    print("  CONL 66%, BIL 33%")
    print("=" * 60)


if __name__ == "__main__":
    main()
