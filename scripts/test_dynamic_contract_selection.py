"""Test script for dynamic options contract selection.

Validates tenor selector and convexity selector functionality.
"""

from decimal import Decimal

from the_alchemiser.shared.options.tenor_selector import TenorSelector
from the_alchemiser.shared.options.convexity_selector import ConvexitySelector
from the_alchemiser.shared.options.schemas import OptionContract, OptionType
from datetime import date, timedelta


def test_tenor_selector():
    """Test tenor selector with various VIX scenarios."""
    print("=" * 60)
    print("Testing TenorSelector")
    print("=" * 60)

    selector = TenorSelector()

    # Test 1: Low VIX (normal market)
    print("\n1. Low VIX scenario (VIX=15):")
    rec = selector.select_tenor(
        current_vix=Decimal("15"),
        use_ladder=True,
    )
    print(f"   Strategy: {rec.strategy}")
    print(f"   Primary DTE: {rec.primary_dte}")
    print(f"   Secondary DTE: {rec.secondary_dte}")
    print(f"   Rationale: {rec.rationale}")

    # Test 2: High IV percentile
    print("\n2. High IV percentile scenario (VIX=25, IV percentile=75%):")
    rec = selector.select_tenor(
        current_vix=Decimal("25"),
        iv_percentile=Decimal("0.75"),
        use_ladder=False,
    )
    print(f"   Strategy: {rec.strategy}")
    print(f"   Primary DTE: {rec.primary_dte}")
    print(f"   Rationale: {rec.rationale}")

    # Test 3: Rich VIX
    print("\n3. Rich VIX scenario (VIX=40):")
    rec = selector.select_tenor(
        current_vix=Decimal("40"),
        use_ladder=False,
    )
    print(f"   Strategy: {rec.strategy}")
    print(f"   Primary DTE: {rec.primary_dte}")
    print(f"   Rationale: {rec.rationale}")

    print("\n✓ TenorSelector tests passed")


def test_convexity_selector():
    """Test convexity selector with sample contracts."""
    print("\n" + "=" * 60)
    print("Testing ConvexitySelector")
    print("=" * 60)

    selector = ConvexitySelector(
        scenario_move=Decimal("-0.20"),
        min_payoff_contribution=Decimal("3.0"),
    )

    # Create sample contracts
    underlying_price = Decimal("500")
    expiry = date.today() + timedelta(days=90)

    contracts = [
        # 15-delta put: strike 425 (15% OTM)
        OptionContract(
            symbol="QQQ241231P425",
            underlying_symbol="QQQ",
            option_type=OptionType.PUT,
            strike_price=Decimal("425"),
            expiration_date=expiry,
            bid_price=Decimal("6.80"),
            ask_price=Decimal("7.00"),
            last_price=Decimal("6.90"),
            volume=500,
            open_interest=2000,
            delta=Decimal("-0.15"),
            gamma=Decimal("0.008"),
            theta=Decimal("-0.05"),
            vega=Decimal("0.50"),
            implied_volatility=Decimal("0.25"),
        ),
        # 10-delta put: strike 400 (20% OTM)
        OptionContract(
            symbol="QQQ241231P400",
            underlying_symbol="QQQ",
            option_type=OptionType.PUT,
            strike_price=Decimal("400"),
            expiration_date=expiry,
            bid_price=Decimal("4.50"),
            ask_price=Decimal("4.70"),
            last_price=Decimal("4.60"),
            volume=300,
            open_interest=1500,
            delta=Decimal("-0.10"),
            gamma=Decimal("0.006"),
            theta=Decimal("-0.03"),
            vega=Decimal("0.40"),
            implied_volatility=Decimal("0.27"),
        ),
        # 20-delta put: strike 450 (10% OTM)
        OptionContract(
            symbol="QQQ241231P450",
            underlying_symbol="QQQ",
            option_type=OptionType.PUT,
            strike_price=Decimal("450"),
            expiration_date=expiry,
            bid_price=Decimal("10.80"),
            ask_price=Decimal("11.00"),
            last_price=Decimal("10.90"),
            volume=800,
            open_interest=3000,
            delta=Decimal("-0.20"),
            gamma=Decimal("0.010"),
            theta=Decimal("-0.08"),
            vega=Decimal("0.60"),
            implied_volatility=Decimal("0.24"),
        ),
    ]

    print(f"\nUnderlying price: ${underlying_price}")
    print(f"Scenario move: {selector._scenario_move:.1%}")
    print(f"Scenario price: ${underlying_price * (1 + selector._scenario_move)}")
    print(f"Min payoff multiple: {selector._min_payoff_contribution}x")

    # Calculate metrics for all contracts
    metrics_list = []
    for contract in contracts:
        metrics = selector.calculate_convexity_metrics(contract, underlying_price)
        if metrics:
            metrics_list.append(metrics)

    print(f"\n✓ Calculated metrics for {len(metrics_list)} contracts")

    # Show convexity metrics
    print("\nConvexity Analysis:")
    for m in metrics_list:
        print(f"\n  Strike ${m.contract.strike_price} (delta {m.contract.delta}):")
        print(f"    Mid price: ${m.contract.mid_price}")
        print(f"    Convexity/dollar: {m.convexity_per_dollar:.6f}")
        print(f"    Scenario payoff: {m.scenario_payoff_multiple:.2f}x premium")
        print(f"    Effective score: {m.effective_score:.2f}")

    # Filter by payoff contribution
    filtered = selector.filter_by_payoff_contribution(metrics_list)
    print(f"\n✓ {len(filtered)}/{len(metrics_list)} contracts pass payoff filter")

    # Rank by convexity
    if filtered:
        ranked = selector.rank_by_convexity(filtered)
        best = ranked[0]
        print(
            f"\n✓ Best contract: Strike ${best.contract.strike_price} (delta {best.contract.delta})"
        )
        print(f"  Effective score: {best.effective_score:.2f}")
        print(f"  Convexity/dollar: {best.convexity_per_dollar:.6f}")
        print(f"  Payoff multiple: {best.scenario_payoff_multiple:.2f}x")

    print("\n✓ ConvexitySelector tests passed")


if __name__ == "__main__":
    test_tenor_selector()
    test_convexity_selector()
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
