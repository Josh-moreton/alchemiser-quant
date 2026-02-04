#!/usr/bin/env python3
"""Debug filter operator behavior with groups.

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

from decimal import Decimal
from engines.dsl.operators.portfolio import (
    _is_portfolio_list,
    _score_portfolio,
    _select_portfolios,
)
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment


def test_is_portfolio_list():
    """Test _is_portfolio_list detection."""
    print("=" * 60)
    print("TEST 1: _is_portfolio_list detection")
    print("=" * 60)

    # Create mock portfolio fragments
    frag1 = PortfolioFragment(
        fragment_id="1",
        source_step="test",
        weights={"SPY": Decimal("0.5"), "QQQ": Decimal("0.5")},
    )
    frag2 = PortfolioFragment(
        fragment_id="2",
        source_step="test",
        weights={"BIL": Decimal("1.0")},
    )

    # Test: list of PortfolioFragments should be detected as portfolio list
    result = _is_portfolio_list([frag1, frag2])
    print(f"List of PortfolioFragments: {result}")
    assert result, "Should detect list of PortfolioFragments"

    # Test: list of strings should NOT be detected as portfolio list
    result = _is_portfolio_list(["SPY", "QQQ", "BIL"])
    print(f"List of strings: {result}")
    assert not result, "Should NOT detect list of strings"

    # Test: empty list
    result = _is_portfolio_list([])
    print(f"Empty list: {result}")
    assert not result, "Should NOT detect empty list"

    print("PASSED!\n")


def test_portfolio_filter_logic():
    """Test the portfolio filtering logic conceptually."""
    print("=" * 60)
    print("TEST 2: Portfolio filter logic")
    print("=" * 60)

    print("The filter operator now has two modes:")
    print("1. Individual assets: extracts all symbols, scores individually")
    print("2. Portfolio mode: treats each PortfolioFragment as a unit")
    print("")
    print("When filter sees [(group ...) (group ...) (group ...)]:")
    print("- Each group evaluates to a PortfolioFragment")
    print("- _is_portfolio_list() detects this case")
    print("- _select_portfolios() scores each portfolio as a unit")
    print("- Uses weighted-average of the condition metric")
    print("- Selects top/bottom N portfolios, merges their weights")
    print("")
    print("This should fix ftl_starburst which uses:")
    print("(filter (moving-average-return {:window 10}) (select-bottom 1) [groups...])")
    print("")


if __name__ == "__main__":
    test_is_portfolio_list()
    test_portfolio_filter_logic()
    print("All tests passed!")
