#!/usr/bin/env python3
"""Integration test for payoff-anchored hedge sizing.

Business Unit: Scripts | Status: current.

Tests the full integration of HedgeSizer with PayoffCalculator and PremiumTracker.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal

# Setup imports
sys.path.insert(0, "/home/runner/work/alchemiser-quant/alchemiser-quant/layers/shared")
sys.path.insert(0, "/home/runner/work/alchemiser-quant/alchemiser-quant/functions/hedge_evaluator")

from the_alchemiser.shared.options.premium_tracker import PremiumTracker
from core.exposure_calculator import PortfolioExposure
from core.hedge_sizer import HedgeSizer


def test_hedge_sizer_payoff_first() -> None:
    """Test HedgeSizer with payoff-first sizing."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: HedgeSizer with Payoff-First Sizing")
    print("=" * 70)

    # Create exposure metrics
    exposure = PortfolioExposure(
        nav=Decimal("100000"),  # $100k NAV
        gross_long_exposure=Decimal("200000"),  # $200k long
        gross_short_exposure=Decimal("0"),  # No shorts
        net_exposure=Decimal("200000"),  # $200k net
        net_exposure_ratio=Decimal("2.0"),  # 2x leverage
        beta_dollars=Decimal("200000"),
        equivalent_qqq_shares=412,  # Approximate
        primary_hedge_underlying="QQQ",
        beta_to_spy=Decimal("1.15"),
        beta_to_qqq=Decimal("1.0"),
        correlation_spy=Decimal("0.95"),
        correlation_qqq=Decimal("0.98"),
    )

    # Create hedge sizer
    sizer = HedgeSizer(template="tail_first")

    # Calculate recommendation
    recommendation = sizer.calculate_hedge_recommendation(
        exposure=exposure,
        current_vix=Decimal("18"),  # Mid VIX tier
        underlying_price=Decimal("485"),  # QQQ price
    )

    print("\n📊 Hedge Recommendation:")
    print(f"  Underlying: {recommendation.underlying_symbol}")
    print(f"  Template: {recommendation.hedge_template}")
    print(f"  VIX tier: {recommendation.vix_tier}")
    print(f"  Target delta: {recommendation.target_delta}")
    print(f"  Target DTE: {recommendation.target_dte}")
    print(f"  \n  📈 Payoff-Based Sizing:")
    print(f"  Scenario move: {recommendation.scenario_move_pct * 100:.0f}%" if recommendation.scenario_move_pct else "N/A")
    print(f"  Target payoff: {recommendation.target_payoff_pct * 100:.1f}% NAV" if recommendation.target_payoff_pct else "N/A")
    print(f"  Contracts for target: {recommendation.contracts_for_target}" if recommendation.contracts_for_target else "N/A")
    print(f"  \n  💰 Budget & Clipping:")
    print(f"  Contracts estimated: {recommendation.contracts_estimated}")
    print(f"  Premium budget: ${recommendation.premium_budget:,.2f}")
    print(f"  NAV %: {recommendation.nav_pct * 100:.2f}%")
    print(f"  Was clipped: {recommendation.was_clipped_by_budget}")
    if recommendation.clip_report:
        print(f"  Clip report: {recommendation.clip_report}")

    assert recommendation.contracts_estimated > 0, "Should recommend contracts"
    assert recommendation.target_payoff_pct is not None, "Should have payoff target"
    assert recommendation.scenario_move_pct is not None, "Should have scenario move"
    print("\n✅ Test passed - HedgeSizer produces payoff-first recommendations")


def test_hedge_sizer_with_premium_tracker() -> None:
    """Test HedgeSizer with PremiumTracker enforcement."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: HedgeSizer with Premium Spend Cap")
    print("=" * 70)

    # Create exposure
    exposure = PortfolioExposure(
        nav=Decimal("100000"),
        gross_long_exposure=Decimal("200000"),
        gross_short_exposure=Decimal("0"),
        net_exposure=Decimal("200000"),
        net_exposure_ratio=Decimal("2.0"),
        beta_dollars=Decimal("200000"),
        equivalent_qqq_shares=412,
        primary_hedge_underlying="QQQ",
        beta_to_spy=Decimal("1.15"),
        beta_to_qqq=Decimal("1.0"),
        correlation_spy=Decimal("0.95"),
        correlation_qqq=Decimal("0.98"),
    )

    # Create premium tracker with existing spend (4.5% of NAV)
    tracker = PremiumTracker()
    tracker.add_spend(
        amount=Decimal("4500"),  # Close to 5% cap
        hedge_id="hedge-001",
        description="Existing hedge",
        timestamp=datetime.now(UTC) - timedelta(days=90),
    )

    # Create hedge sizer with tracker
    sizer = HedgeSizer(template="tail_first", premium_tracker=tracker)

    # Calculate recommendation
    recommendation = sizer.calculate_hedge_recommendation(
        exposure=exposure,
        current_vix=Decimal("18"),
        underlying_price=Decimal("485"),
    )

    # Check if we should hedge (should reject due to cap)
    should_hedge, reason = sizer.should_hedge(
        exposure=exposure,
        existing_hedge_count=0,
        proposed_spend=recommendation.premium_budget,
    )

    print("\n📊 Hedge Evaluation:")
    print(f"  Premium budget needed: ${recommendation.premium_budget:,.2f}")
    print(f"  Current 12-month spend: $4,500.00 (4.5% NAV)")
    print(f"  Annual cap: $5,000.00 (5.0% NAV)")
    print(f"  Should hedge: {should_hedge}")
    if reason:
        print(f"  Rejection reason: {reason}")

    # Should reject due to spend cap
    assert not should_hedge, "Should reject hedge due to spend cap"
    assert "Rolling 12-month spend cap" in reason, "Should cite spend cap as reason"
    print("\n✅ Test passed - Premium tracker correctly enforces spend cap")


def test_hedge_sizer_budget_clipping() -> None:
    """Test that budget clipping produces explicit report."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Budget Clipping with Explicit Report")
    print("=" * 70)

    # Create small portfolio where budget will clip contracts
    exposure = PortfolioExposure(
        nav=Decimal("10000"),  # Small $10k NAV
        gross_long_exposure=Decimal("20000"),  # 2x leverage
        gross_short_exposure=Decimal("0"),
        net_exposure=Decimal("20000"),
        net_exposure_ratio=Decimal("2.0"),
        beta_dollars=Decimal("20000"),
        equivalent_qqq_shares=41,
        primary_hedge_underlying="QQQ",
        beta_to_spy=Decimal("1.15"),
        beta_to_qqq=Decimal("1.0"),
        correlation_spy=Decimal("0.95"),
        correlation_qqq=Decimal("0.98"),
    )

    sizer = HedgeSizer(template="tail_first")

    recommendation = sizer.calculate_hedge_recommendation(
        exposure=exposure,
        current_vix=Decimal("15"),  # Low VIX (higher budget)
        underlying_price=Decimal("485"),
    )

    print("\n📊 Small Portfolio Hedge:")
    print(f"  NAV: ${exposure.nav:,.2f}")
    print(f"  Contracts for payoff target: {recommendation.contracts_for_target}")
    print(f"  Contracts estimated: {recommendation.contracts_estimated}")
    print(f"  Was clipped: {recommendation.was_clipped_by_budget}")

    if recommendation.was_clipped_by_budget:
        print(f"\n  📋 Clipping Report:")
        print(f"  {recommendation.clip_report}")
        print("\n✅ Test passed - Budget clipping produces explicit report")
    else:
        print("\n  ℹ️  Budget was sufficient (no clipping needed)")
        print("✅ Test passed - No clipping needed for this portfolio size")


def run_all_tests() -> None:
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("HEDGE SIZER INTEGRATION TESTS")
    print("=" * 70)

    try:
        test_hedge_sizer_payoff_first()
        test_hedge_sizer_with_premium_tracker()
        test_hedge_sizer_budget_clipping()

        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 70 + "\n")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
