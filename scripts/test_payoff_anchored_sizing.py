#!/usr/bin/env python3
"""Test payoff-anchored sizing and premium tracking.

Business Unit: Scripts | Status: current.

Tests the new payoff-first sizing approach for options hedging.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal

# Setup imports
sys.path.insert(0, "/home/runner/work/alchemiser-quant/alchemiser-quant/layers/shared")

from the_alchemiser.shared.options.payoff_calculator import (
    PayoffCalculator,
    PayoffScenario,
)
from the_alchemiser.shared.options.premium_tracker import (
    PremiumSpendRecord,
    PremiumTracker,
)


def test_payoff_calculator() -> None:
    """Test PayoffCalculator for scenario-based sizing."""
    print("\n" + "=" * 70)
    print("TEST 1: PayoffCalculator - Basic Scenario")
    print("=" * 70)

    calc = PayoffCalculator()

    # Test basic -20% scenario with 8% target payoff
    scenario = PayoffScenario(
        scenario_move_pct=Decimal("-0.20"),
        target_payoff_pct=Decimal("0.08"),
        description="-20% market crash",
    )

    result = calc.calculate_contracts_for_scenario(
        underlying_price=Decimal("500"),
        option_delta=Decimal("0.15"),
        scenario=scenario,
        nav=Decimal("100000"),
        leverage_factor=Decimal("1.0"),
    )

    print(f"  Underlying price: ${result.underlying_price}")
    print(f"  Option delta: {result.option_delta}")
    print(f"  Scenario move: {result.scenario_move_pct * 100}%")
    print(f"  Target payoff: {result.target_payoff_pct * 100}% of NAV")
    print(f"  Target payoff $: ${result.target_payoff_dollars:,.2f}")
    print(f"  Estimated strike: ${result.estimated_strike:.2f}")
    print(f"  Scenario price: ${result.scenario_price:.2f}")
    print(f"  Payoff per contract: ${result.payoff_per_contract:.2f}")
    print(f"  Contracts required: {result.contracts_required}")

    # Verify calculation
    # Strike = 500 * (1 - 0.15) = 425
    # Scenario price = 500 * 0.80 = 400
    # Payoff per contract = (425 - 400) * 100 = 2,500
    # Target payoff = 100,000 * 0.08 = 8,000
    # Contracts = 8,000 / 2,500 = 3.2 ≈ 4 (rounded up)
    assert 3 <= result.contracts_required <= 4, f"Expected 3-4 contracts, got {result.contracts_required}"
    print("✅ Test passed")


def test_payoff_calculator_with_leverage() -> None:
    """Test PayoffCalculator with portfolio leverage."""
    print("\n" + "=" * 70)
    print("TEST 2: PayoffCalculator - With 2x Leverage")
    print("=" * 70)

    calc = PayoffCalculator()

    scenario = PayoffScenario(
        scenario_move_pct=Decimal("-0.20"),
        target_payoff_pct=Decimal("0.08"),
        description="-20% market crash",
    )

    result = calc.calculate_contracts_for_scenario(
        underlying_price=Decimal("500"),
        option_delta=Decimal("0.15"),
        scenario=scenario,
        nav=Decimal("100000"),
        leverage_factor=Decimal("2.0"),  # 2x leverage
    )

    print(f"  Leverage factor: 2.0x")
    print(f"  Adjusted target payoff: {result.target_payoff_pct * 100}% of NAV")
    print(f"  Contracts required: {result.contracts_required}")

    # With 2x leverage, target payoff is scaled up
    # Target = 8% * 2.0 = 16% of NAV = $16,000
    # Contracts = 16,000 / 2,500 = 6.4 ≈ 7
    assert 6 <= result.contracts_required <= 7, f"Expected 6-7 contracts, got {result.contracts_required}"
    print("✅ Test passed")


def test_premium_cost_estimation() -> None:
    """Test premium cost estimation."""
    print("\n" + "=" * 70)
    print("TEST 3: Premium Cost Estimation")
    print("=" * 70)

    calc = PayoffCalculator()

    # Estimate premium for 3 contracts
    premium = calc.estimate_premium_cost(
        contracts=3,
        underlying_price=Decimal("500"),
        option_delta=Decimal("0.15"),
        days_to_expiry=90,
        is_spread=False,
    )

    print(f"  Contracts: 3")
    print(f"  Underlying: $500")
    print(f"  Delta: 0.15 (15-delta)")
    print(f"  DTE: 90 days")
    print(f"  Estimated premium: ${premium:,.2f}")

    # 15-delta put at 90 DTE ≈ 1.5% of underlying
    # Per contract: 500 * 0.015 * 100 = $750
    # Total: $750 * 3 = $2,250
    expected_min = Decimal("2000")
    expected_max = Decimal("2500")
    assert expected_min <= premium <= expected_max, f"Expected ${expected_min}-${expected_max}, got ${premium}"
    print("✅ Test passed")


def test_premium_tracker_basic() -> None:
    """Test PremiumTracker basic functionality."""
    print("\n" + "=" * 70)
    print("TEST 4: PremiumTracker - Basic Tracking")
    print("=" * 70)

    tracker = PremiumTracker()

    # Add some spend records
    now = datetime.now(UTC)
    tracker.add_spend(
        amount=Decimal("1000"),
        hedge_id="hedge-001",
        description="Tail hedge #1",
        timestamp=now - timedelta(days=30),
    )
    tracker.add_spend(
        amount=Decimal("1500"),
        hedge_id="hedge-002",
        description="Tail hedge #2",
        timestamp=now - timedelta(days=60),
    )

    # Get rolling 12-month spend
    total_spend = tracker.get_rolling_12mo_spend()

    print(f"  Spend #1: $1,000 (30 days ago)")
    print(f"  Spend #2: $1,500 (60 days ago)")
    print(f"  Total 12-month spend: ${total_spend:,.2f}")

    assert total_spend == Decimal("2500"), f"Expected $2,500, got ${total_spend}"
    print("✅ Test passed")


def test_premium_tracker_cap_enforcement() -> None:
    """Test PremiumTracker spend cap enforcement."""
    print("\n" + "=" * 70)
    print("TEST 5: PremiumTracker - Cap Enforcement")
    print("=" * 70)

    tracker = PremiumTracker()
    nav = Decimal("100000")  # $100k NAV

    # Add existing spend (4% of NAV)
    now = datetime.now(UTC)
    tracker.add_spend(
        amount=Decimal("4000"),
        hedge_id="hedge-001",
        description="Existing hedges",
        timestamp=now - timedelta(days=180),
    )

    # Proposed spend that would push over 5% cap
    proposed = Decimal("2000")  # Would make total 6%

    check_result = tracker.check_spend_within_cap(
        proposed_spend=proposed,
        nav=nav,
    )

    print(f"  NAV: ${nav:,.2f}")
    print(f"  Current 12-month spend: ${check_result.current_spend_12mo:,.2f} ({check_result.current_spend_pct * 100:.1f}%)")
    print(f"  Proposed additional: ${proposed:,.2f}")
    print(f"  Total after: ${check_result.total_spend_after:,.2f} ({check_result.total_spend_pct * 100:.1f}%)")
    print(f"  Annual cap: ${check_result.annual_cap_dollars:,.2f} (5.0%)")
    print(f"  Is within cap: {check_result.is_within_cap}")

    # 5% cap = $5,000
    # Current = $4,000
    # Proposed = $2,000
    # Total = $6,000 > $5,000 → should FAIL
    assert not check_result.is_within_cap, "Should exceed cap"
    assert check_result.annual_cap_dollars == Decimal("5000")
    print("✅ Test passed - correctly rejects spend over cap")


def test_premium_tracker_within_cap() -> None:
    """Test PremiumTracker when spend is within cap."""
    print("\n" + "=" * 70)
    print("TEST 6: PremiumTracker - Within Cap")
    print("=" * 70)

    tracker = PremiumTracker()
    nav = Decimal("100000")

    # Add existing spend (2% of NAV)
    now = datetime.now(UTC)
    tracker.add_spend(
        amount=Decimal("2000"),
        hedge_id="hedge-001",
        description="Existing hedges",
        timestamp=now - timedelta(days=90),
    )

    # Proposed spend that stays within 5% cap
    proposed = Decimal("2000")  # Would make total 4%

    check_result = tracker.check_spend_within_cap(
        proposed_spend=proposed,
        nav=nav,
    )

    print(f"  Current 12-month spend: ${check_result.current_spend_12mo:,.2f} ({check_result.current_spend_pct * 100:.1f}%)")
    print(f"  Proposed additional: ${proposed:,.2f}")
    print(f"  Total after: ${check_result.total_spend_after:,.2f} ({check_result.total_spend_pct * 100:.1f}%)")
    print(f"  Annual cap: ${check_result.annual_cap_dollars:,.2f} (5.0%)")
    print(f"  Remaining capacity: ${check_result.remaining_capacity:,.2f}")
    print(f"  Is within cap: {check_result.is_within_cap}")

    # Total = $4,000 < $5,000 → should PASS
    assert check_result.is_within_cap, "Should be within cap"
    assert check_result.remaining_capacity == Decimal("3000")  # $5,000 cap - $2,000 current = $3,000
    print("✅ Test passed - correctly accepts spend within cap")


def test_premium_tracker_rolling_window() -> None:
    """Test PremiumTracker rolling window (old spend expires)."""
    print("\n" + "=" * 70)
    print("TEST 7: PremiumTracker - Rolling Window")
    print("=" * 70)

    tracker = PremiumTracker()

    now = datetime.now(UTC)

    # Add spend from 13 months ago (should NOT count)
    tracker.add_spend(
        amount=Decimal("1000"),
        hedge_id="hedge-old",
        description="Old hedge (expired from window)",
        timestamp=now - timedelta(days=395),  # 13 months ago
    )

    # Add spend from 6 months ago (should count)
    tracker.add_spend(
        amount=Decimal("2000"),
        hedge_id="hedge-recent",
        description="Recent hedge",
        timestamp=now - timedelta(days=180),
    )

    total_spend = tracker.get_rolling_12mo_spend()

    print(f"  Spend 13 months ago: $1,000 (EXPIRED)")
    print(f"  Spend 6 months ago: $2,000 (COUNTED)")
    print(f"  Total 12-month spend: ${total_spend:,.2f}")

    assert total_spend == Decimal("2000"), f"Expected $2,000 (old spend expired), got ${total_spend}"
    print("✅ Test passed - correctly excludes spend outside window")


def run_all_tests() -> None:
    """Run all test cases."""
    print("\n" + "=" * 70)
    print("PAYOFF-ANCHORED SIZING & PREMIUM TRACKING TESTS")
    print("=" * 70)

    try:
        test_payoff_calculator()
        test_payoff_calculator_with_leverage()
        test_premium_cost_estimation()
        test_premium_tracker_basic()
        test_premium_tracker_cap_enforcement()
        test_premium_tracker_within_cap()
        test_premium_tracker_rolling_window()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70 + "\n")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
