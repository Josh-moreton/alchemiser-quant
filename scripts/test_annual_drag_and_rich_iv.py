#!/usr/bin/env python3
"""Test script for annual drag calculations and rich IV reduction logic.

This script validates:
1. Annual drag calculations at different leverage levels
2. Rich IV detection and adjustment logic
3. Annual spend cap enforcement
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

# Add shared layer to path
sys.path.insert(0, str(Path(__file__).parent.parent / "layers" / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "functions" / "hedge_evaluator"))

from the_alchemiser.shared.options.constants import (
    MAX_ANNUAL_PREMIUM_SPEND_PCT,
    RICH_IV_THRESHOLD,
    TAIL_HEDGE_TEMPLATE,
    apply_rich_iv_adjustment,
    calculate_annual_drag,
    check_annual_spend_cap,
    get_exposure_multiplier,
    should_reduce_hedge_intensity,
)

# Import after path setup
from core.hedge_sizer import HedgeSizer


@dataclass(frozen=True)
class MockExposure:
    """Mock portfolio exposure for testing."""

    nav: Decimal
    net_exposure_ratio: Decimal
    primary_hedge_underlying: str
    portfolio_beta_to_spy: Decimal = Decimal("1.0")


def test_annual_drag_calculations() -> None:
    """Test annual drag calculations at different leverage levels."""
    print("\n=== Test 1: Annual Drag Calculations ===")

    # Monthly rate for low VIX: 0.8% NAV/month
    monthly_rate = TAIL_HEDGE_TEMPLATE.budget_vix_low

    # Test at 1.0x leverage
    leverage_1x = Decimal("1.0")
    drag_1x = calculate_annual_drag(monthly_rate, leverage_1x)
    print(f"At 1.0x leverage: {drag_1x * 100:.2f}% annual drag")
    assert drag_1x == Decimal("0.096"), "Expected 9.6% at 1.0x"

    # Test at 2.0x leverage
    leverage_2x = Decimal("2.0")
    drag_2x = calculate_annual_drag(monthly_rate, leverage_2x)
    print(f"At 2.0x leverage: {drag_2x * 100:.2f}% annual drag")
    assert drag_2x == Decimal("0.144"), "Expected 14.4% at 2.0x (1.5x multiplier)"

    # Test at 2.5x leverage
    leverage_2_5x = Decimal("2.5")
    multiplier_2_5x = get_exposure_multiplier(leverage_2_5x)
    drag_2_5x = calculate_annual_drag(monthly_rate, leverage_2_5x)
    print(f"At 2.5x leverage: {drag_2_5x * 100:.2f}% annual drag (multiplier: {multiplier_2_5x})")

    print("✅ Annual drag calculations working correctly")


def test_rich_iv_detection() -> None:
    """Test rich IV detection logic."""
    print("\n=== Test 2: Rich IV Detection ===")

    # Normal VIX should not trigger reduction
    normal_vix = Decimal("25")
    assert not should_reduce_hedge_intensity(normal_vix), "Normal VIX should not trigger reduction"
    print(f"VIX {normal_vix}: No reduction ✓")

    # Rich VIX should trigger reduction
    rich_vix = Decimal("40")
    assert should_reduce_hedge_intensity(rich_vix), "Rich VIX should trigger reduction"
    print(f"VIX {rich_vix}: Reduction triggered ✓")

    # Edge case: exactly at threshold
    threshold_vix = RICH_IV_THRESHOLD
    assert not should_reduce_hedge_intensity(
        threshold_vix
    ), "At threshold should not trigger (> not >=)"
    print(f"VIX {threshold_vix} (threshold): No reduction ✓")

    print("✅ Rich IV detection working correctly")


def test_rich_iv_adjustments() -> None:
    """Test rich IV parameter adjustments."""
    print("\n=== Test 3: Rich IV Adjustments ===")

    # Original parameters
    target_delta = Decimal("0.15")
    target_dte = 90
    target_payoff_pct = Decimal("0.08")
    rich_vix = Decimal("40")

    # Apply adjustments
    adj_delta, adj_dte, adj_payoff = apply_rich_iv_adjustment(
        target_delta=target_delta,
        target_dte=target_dte,
        target_payoff_pct=target_payoff_pct,
        vix=rich_vix,
    )

    print(f"Original delta: {target_delta}, DTE: {target_dte}, Payoff: {target_payoff_pct * 100}%")
    print(f"Adjusted delta: {adj_delta}, DTE: {adj_dte}, Payoff: {adj_payoff * 100}%")

    # Verify adjustments
    assert adj_delta < target_delta, "Delta should be widened (reduced)"
    assert adj_dte > target_dte, "DTE should be extended"
    assert adj_payoff < target_payoff_pct, "Payoff should be reduced"

    # Expected values
    assert adj_delta == Decimal("0.10"), f"Expected 10-delta, got {adj_delta}"
    assert adj_dte == 120, f"Expected 120 DTE, got {adj_dte}"
    assert adj_payoff == Decimal("0.06"), f"Expected 6% payoff, got {adj_payoff}"

    print("✅ Rich IV adjustments working correctly")


def test_annual_spend_cap() -> None:
    """Test annual spend cap enforcement."""
    print("\n=== Test 4: Annual Spend Cap Enforcement ===")

    nav = Decimal("100000")
    max_annual = nav * MAX_ANNUAL_PREMIUM_SPEND_PCT

    # Case 1: Well under cap
    ytd_spend = Decimal("2000")  # 2% of NAV
    proposed = Decimal("1000")  # 1% of NAV
    result = check_annual_spend_cap(ytd_spend, proposed, nav)
    assert result, "Should allow spend under cap"
    print(f"YTD: ${ytd_spend}, Proposed: ${proposed}, Total: ${ytd_spend + proposed} - ALLOWED ✓")

    # Case 2: At cap
    ytd_spend = Decimal("4000")  # 4% of NAV
    proposed = Decimal("1000")  # 1% of NAV (total = 5%)
    result = check_annual_spend_cap(ytd_spend, proposed, nav)
    assert result, "Should allow spend at cap"
    print(f"YTD: ${ytd_spend}, Proposed: ${proposed}, Total: ${ytd_spend + proposed} - ALLOWED ✓")

    # Case 3: Over cap
    ytd_spend = Decimal("4500")  # 4.5% of NAV
    proposed = Decimal("600")  # 0.6% of NAV (total = 5.1%)
    result = check_annual_spend_cap(ytd_spend, proposed, nav)
    assert not result, "Should reject spend over cap"
    print(f"YTD: ${ytd_spend}, Proposed: ${proposed}, Total: ${ytd_spend + proposed} - REJECTED ✓")

    print("✅ Annual spend cap enforcement working correctly")


def test_hedge_sizer_with_annual_cap() -> None:
    """Test HedgeSizer integration with annual spend cap."""
    print("\n=== Test 5: HedgeSizer with Annual Cap ===")

    sizer = HedgeSizer()

    # Portfolio with $100k NAV, 2x leverage
    exposure = MockExposure(
        nav=Decimal("100000"),
        net_exposure_ratio=Decimal("2.0"),
        primary_hedge_underlying="QQQ",
    )

    # Case 1: Normal conditions - should hedge
    ytd_spend = Decimal("2000")  # 2% of NAV
    should_hedge, skip_reason = sizer.should_hedge(
        exposure=exposure,
        existing_hedge_count=0,
        year_to_date_spend=ytd_spend,
        proposed_spend=Decimal("1000"),  # 1% more
    )
    assert should_hedge, "Should hedge when under annual cap"
    print(f"YTD spend: ${ytd_spend}, Proposed: $1000 - HEDGE ALLOWED ✓")

    # Case 2: Annual cap exceeded - should skip
    ytd_spend = Decimal("5000")  # 5% of NAV (at cap)
    should_hedge, skip_reason = sizer.should_hedge(
        exposure=exposure,
        existing_hedge_count=0,
        year_to_date_spend=ytd_spend,
        proposed_spend=Decimal("500"),  # Would exceed cap
    )
    assert not should_hedge, "Should skip when annual cap would be exceeded"
    assert "Annual spend cap" in skip_reason, f"Expected cap message, got: {skip_reason}"
    print(f"YTD spend: ${ytd_spend}, Proposed: $500 - HEDGE SKIPPED ✓")
    print(f"Skip reason: {skip_reason}")

    print("✅ HedgeSizer annual cap integration working correctly")


def test_hedge_sizer_with_rich_iv() -> None:
    """Test HedgeSizer integration with rich IV adjustments."""
    print("\n=== Test 6: HedgeSizer with Rich IV ===")

    sizer = HedgeSizer()

    exposure = MockExposure(
        nav=Decimal("100000"),
        net_exposure_ratio=Decimal("2.0"),
        primary_hedge_underlying="QQQ",
    )

    # Normal VIX - no adjustments
    normal_vix = Decimal("20")
    normal_rec = sizer.calculate_hedge_recommendation(
        exposure=exposure,
        current_vix=normal_vix,
        underlying_price=Decimal("485"),
    )
    print(f"\nNormal VIX ({normal_vix}):")
    print(f"  Delta: {normal_rec.target_delta}, DTE: {normal_rec.target_dte}")

    # Rich VIX - should apply adjustments
    rich_vix = Decimal("40")
    rich_rec = sizer.calculate_hedge_recommendation(
        exposure=exposure,
        current_vix=rich_vix,
        underlying_price=Decimal("485"),
    )
    print(f"\nRich VIX ({rich_vix}):")
    print(f"  Delta: {rich_rec.target_delta}, DTE: {rich_rec.target_dte}")

    # Verify adjustments were applied
    assert rich_rec.target_delta < normal_rec.target_delta, "Delta should be wider for rich IV"
    assert rich_rec.target_dte > normal_rec.target_dte, "DTE should be extended for rich IV"

    print("✅ HedgeSizer rich IV integration working correctly")


def main() -> None:
    """Run all tests."""
    print("=" * 80)
    print("Annual Drag and Rich IV Test Suite")
    print("=" * 80)

    try:
        test_annual_drag_calculations()
        test_rich_iv_detection()
        test_rich_iv_adjustments()
        test_annual_spend_cap()
        test_hedge_sizer_with_annual_cap()
        test_hedge_sizer_with_rich_iv()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
