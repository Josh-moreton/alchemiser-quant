#!/usr/bin/env python3
"""Test scenario-payoff contract sizing for options hedging.

Business Unit: Scripts | Status: current.

Tests the calculate_contracts_for_payoff_target function with various scenarios.
"""
import sys
from decimal import Decimal


def calculate_contracts_for_payoff_target_test(
    underlying_price: Decimal,
    option_delta: Decimal,
    scenario_move: Decimal,
    target_payoff: Decimal,
    nav: Decimal,
) -> int:
    """Test implementation of contract sizing function.

    This is a standalone test implementation to verify the logic
    without dependencies on the full shared layer.
    """
    # Target NAV payoff in dollars
    target_payoff_dollars = nav * target_payoff

    # Calculate scenario price after the move
    scenario_price = underlying_price * (Decimal("1") + scenario_move)

    # Estimate strike from delta
    delta_to_otm_pct = option_delta
    strike = underlying_price * (Decimal("1") - delta_to_otm_pct)

    # Calculate option payoff per contract for scenario move
    option_payoff_per_contract = max(Decimal("0"), strike - scenario_price) * 100

    # Avoid division by zero
    if option_payoff_per_contract <= 0:
        return 1

    # Calculate required contracts
    contracts = target_payoff_dollars / option_payoff_per_contract

    # Round up and ensure minimum 1 contract
    contracts_int = max(1, int(contracts + Decimal("0.5")))

    return contracts_int


def test_basic_scenario() -> None:
    """Test basic -20% scenario with 8% target payoff."""
    print("\n=== Test 1: Basic Scenario ===")
    print("QQQ at $500, 15-delta put, -20% move → +8% NAV target")
    print("Portfolio NAV: $100,000")

    contracts = calculate_contracts_for_payoff_target_test(
        underlying_price=Decimal("500"),
        option_delta=Decimal("0.15"),
        scenario_move=Decimal("-0.20"),
        target_payoff=Decimal("0.08"),
        nav=Decimal("100000"),
    )

    print(f"Result: {contracts} contracts")
    print(f"Expected: ~100 contracts")

    # Verify calculation
    # Strike = 500 * (1 - 0.15) = 425
    # Scenario price = 500 * 0.80 = 400
    # Payoff per contract = (425 - 400) * 100 = 2,500
    # Target payoff = 100,000 * 0.08 = 8,000
    # Contracts = 8,000 / 2,500 = 3.2 ≈ 3
    assert 3 <= contracts <= 4, f"Expected 3-4 contracts, got {contracts}"
    print("✓ Test passed")


def test_larger_portfolio() -> None:
    """Test with larger portfolio ($1M NAV)."""
    print("\n=== Test 2: Larger Portfolio ===")
    print("QQQ at $485, 15-delta put, -20% move → +6% NAV target")
    print("Portfolio NAV: $1,000,000")

    contracts = calculate_contracts_for_payoff_target_test(
        underlying_price=Decimal("485"),
        option_delta=Decimal("0.15"),
        scenario_move=Decimal("-0.20"),
        target_payoff=Decimal("0.06"),
        nav=Decimal("1000000"),
    )

    print(f"Result: {contracts} contracts")

    # Verify calculation
    # Strike = 485 * 0.85 = 412.25
    # Scenario price = 485 * 0.80 = 388
    # Payoff per contract = (412.25 - 388) * 100 = 2,425
    # Target payoff = 1,000,000 * 0.06 = 60,000
    # Contracts = 60,000 / 2,425 ≈ 24.7 ≈ 25
    assert 24 <= contracts <= 26, f"Expected 24-26 contracts, got {contracts}"
    print("✓ Test passed")


def test_different_delta() -> None:
    """Test with different delta (10-delta, more OTM)."""
    print("\n=== Test 3: Different Delta (10-delta) ===")
    print("QQQ at $500, 10-delta put, -20% move → +8% NAV target")
    print("Portfolio NAV: $100,000")

    contracts = calculate_contracts_for_payoff_target_test(
        underlying_price=Decimal("500"),
        option_delta=Decimal("0.10"),
        scenario_move=Decimal("-0.20"),
        target_payoff=Decimal("0.08"),
        nav=Decimal("100000"),
    )

    print(f"Result: {contracts} contracts")

    # Verify calculation
    # Strike = 500 * 0.90 = 450
    # Scenario price = 500 * 0.80 = 400
    # Payoff per contract = (450 - 400) * 100 = 5,000
    # Target payoff = 100,000 * 0.08 = 8,000
    # Contracts = 8,000 / 5,000 = 1.6 ≈ 2
    assert 1 <= contracts <= 2, f"Expected 1-2 contracts, got {contracts}"
    print("✓ Test passed")


def test_severe_crash() -> None:
    """Test with more severe crash scenario (-30%)."""
    print("\n=== Test 4: Severe Crash Scenario ===")
    print("QQQ at $500, 15-delta put, -30% move → +10% NAV target")
    print("Portfolio NAV: $100,000")

    contracts = calculate_contracts_for_payoff_target_test(
        underlying_price=Decimal("500"),
        option_delta=Decimal("0.15"),
        scenario_move=Decimal("-0.30"),
        target_payoff=Decimal("0.10"),
        nav=Decimal("100000"),
    )

    print(f"Result: {contracts} contracts")

    # Verify calculation
    # Strike = 500 * 0.85 = 425
    # Scenario price = 500 * 0.70 = 350
    # Payoff per contract = (425 - 350) * 100 = 7,500
    # Target payoff = 100,000 * 0.10 = 10,000
    # Contracts = 10,000 / 7,500 = 1.33 ≈ 1
    assert 1 <= contracts <= 2, f"Expected 1-2 contracts, got {contracts}"
    print("✓ Test passed")


def test_small_portfolio() -> None:
    """Test with small portfolio ($10k NAV)."""
    print("\n=== Test 5: Small Portfolio ===")
    print("QQQ at $500, 15-delta put, -20% move → +8% NAV target")
    print("Portfolio NAV: $10,000")

    contracts = calculate_contracts_for_payoff_target_test(
        underlying_price=Decimal("500"),
        option_delta=Decimal("0.15"),
        scenario_move=Decimal("-0.20"),
        target_payoff=Decimal("0.08"),
        nav=Decimal("10000"),
    )

    print(f"Result: {contracts} contracts")

    # Verify calculation
    # Strike = 500 * 0.85 = 425
    # Scenario price = 500 * 0.80 = 400
    # Payoff per contract = (425 - 400) * 100 = 2,500
    # Target payoff = 10,000 * 0.08 = 800
    # Contracts = 800 / 2,500 = 0.32 → minimum 1
    assert contracts == 1, f"Expected 1 contract (minimum), got {contracts}"
    print("✓ Test passed")


def test_edge_case_zero_payoff() -> None:
    """Test edge case where scenario price exceeds strike (no payoff)."""
    print("\n=== Test 6: Edge Case - Scenario Price Above Strike ===")
    print("QQQ at $500, 5-delta put, -4% move → +2% NAV target")
    print("Portfolio NAV: $100,000")
    print("(Strike at 475, scenario price at 480 - put expires worthless)")

    contracts = calculate_contracts_for_payoff_target_test(
        underlying_price=Decimal("500"),
        option_delta=Decimal("0.05"),
        scenario_move=Decimal("-0.04"),
        target_payoff=Decimal("0.02"),
        nav=Decimal("100000"),
    )

    print(f"Result: {contracts} contracts")
    # Should return minimum 1 contract even though payoff is zero
    assert contracts == 1, f"Expected 1 contract (minimum for zero payoff), got {contracts}"
    print("✓ Test passed (returns minimum 1 contract)")


def test_spy_example() -> None:
    """Test with SPY instead of QQQ."""
    print("\n=== Test 7: SPY Example ===")
    print("SPY at $590, 15-delta put, -20% move → +7% NAV target")
    print("Portfolio NAV: $250,000")

    contracts = calculate_contracts_for_payoff_target_test(
        underlying_price=Decimal("590"),
        option_delta=Decimal("0.15"),
        scenario_move=Decimal("-0.20"),
        target_payoff=Decimal("0.07"),
        nav=Decimal("250000"),
    )

    print(f"Result: {contracts} contracts")

    # Verify calculation
    # Strike = 590 * 0.85 = 501.5
    # Scenario price = 590 * 0.80 = 472
    # Payoff per contract = (501.5 - 472) * 100 = 2,950
    # Target payoff = 250,000 * 0.07 = 17,500
    # Contracts = 17,500 / 2,950 ≈ 5.9 ≈ 6
    assert 5 <= contracts <= 7, f"Expected 5-7 contracts, got {contracts}"
    print("✓ Test passed")


def run_all_tests() -> None:
    """Run all test cases."""
    print("\n" + "=" * 60)
    print("Testing calculate_contracts_for_payoff_target_test()")
    print("=" * 60)

    try:
        test_basic_scenario()
        test_larger_portfolio()
        test_different_delta()
        test_severe_crash()
        test_small_portfolio()
        test_edge_case_zero_payoff()
        test_spy_example()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60 + "\n")
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
