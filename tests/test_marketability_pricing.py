"""Tests for marketability pricing algorithm.

Tests the adaptive limit pricing with recorded market snapshots.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from the_alchemiser.shared.options.marketability_pricing import (
    MarketabilityPricer,
    MarketSnapshot,
    OrderSide,
    SlippageTracker,
)
from the_alchemiser.shared.options.schemas import OptionContract, OptionType


def create_test_contract(
    bid: Decimal,
    ask: Decimal,
    symbol: str = "SPY241231P00450000",
) -> OptionContract:
    """Create a test option contract with bid/ask."""
    mid = (bid + ask) / Decimal("2")
    return OptionContract(
        symbol=symbol,
        underlying_symbol="SPY",
        option_type=OptionType.PUT,
        strike_price=Decimal("450"),
        expiration_date=date(2024, 12, 31),
        bid_price=bid,
        ask_price=ask,
        mid_price=mid,
        last_price=mid,
        volume=100,
        open_interest=1000,
        delta=Decimal("-0.15"),
        gamma=None,
        theta=None,
        vega=None,
        implied_volatility=None,
    )


class TestMarketabilityPricer:
    """Test marketability pricing algorithm."""

    def test_initial_limit_at_mid(self) -> None:
        """Test that initial limit price starts at mid."""
        contract = create_test_contract(bid=Decimal("1.00"), ask=Decimal("1.10"))
        pricer = MarketabilityPricer()

        initial_limit = pricer.calculate_initial_limit_price(
            contract=contract,
            order_side=OrderSide.OPEN,
            vix_level=None,
        )

        # Should start at mid price
        assert initial_limit == Decimal("1.05")

    def test_price_stepping_toward_ask(self) -> None:
        """Test that price steps toward ask in increments."""
        contract = create_test_contract(bid=Decimal("1.00"), ask=Decimal("1.10"))
        pricer = MarketabilityPricer()

        initial_limit = pricer.calculate_initial_limit_price(
            contract=contract,
            order_side=OrderSide.OPEN,
            vix_level=None,
        )

        # Step once (calm market: 10% of spread)
        next_limit = pricer.calculate_next_limit_price(
            current_limit=initial_limit,
            contract=contract,
            order_side=OrderSide.OPEN,
            vix_level=Decimal("20"),  # Calm
            attempt_number=2,
        )

        assert next_limit is not None
        # Spread = 0.10, 10% of spread = 0.01
        # Next limit = 1.05 + 0.01 = 1.06
        assert next_limit == Decimal("1.06")

    def test_high_iv_larger_steps(self) -> None:
        """Test that high IV conditions use larger price steps."""
        contract = create_test_contract(bid=Decimal("1.00"), ask=Decimal("1.10"))
        pricer = MarketabilityPricer()

        initial_limit = Decimal("1.05")

        # Step in high IV (20% of spread)
        next_limit = pricer.calculate_next_limit_price(
            current_limit=initial_limit,
            contract=contract,
            order_side=OrderSide.OPEN,
            vix_level=Decimal("30"),  # High IV (>= 28)
            attempt_number=2,
        )

        assert next_limit is not None
        # Spread = 0.10, 20% of spread = 0.02
        # Next limit = 1.05 + 0.02 = 1.07
        assert next_limit == Decimal("1.07")

    def test_max_slippage_per_trade_open(self) -> None:
        """Test that max slippage per trade is enforced for opens."""
        # Large spread to test slippage limit
        contract = create_test_contract(bid=Decimal("1.00"), ask=Decimal("2.00"))
        pricer = MarketabilityPricer()

        current_limit = Decimal("1.50")  # Mid price

        # Try to step way past max slippage (10% for opens)
        # Max slippage from mid = 1.50 * 1.10 = 1.65
        for _ in range(10):
            next_limit = pricer.calculate_next_limit_price(
                current_limit=current_limit,
                contract=contract,
                order_side=OrderSide.OPEN,
                vix_level=None,
                attempt_number=2,
            )
            if next_limit is None:
                # Hit slippage limit
                break
            current_limit = next_limit

        # Should stop before reaching ask (2.00)
        assert current_limit < Decimal("1.66")

    def test_max_slippage_per_trade_close(self) -> None:
        """Test that max slippage per trade is tighter for closes."""
        # Close positions should have tighter slippage (5% vs 10%)
        contract = create_test_contract(bid=Decimal("1.00"), ask=Decimal("1.50"))
        pricer = MarketabilityPricer()

        current_limit = Decimal("1.25")  # Mid price

        # Try to step past max slippage (5% for closes)
        # Max slippage from mid = 1.25 * 1.05 = 1.3125
        for _ in range(10):
            next_limit = pricer.calculate_next_limit_price(
                current_limit=current_limit,
                contract=contract,
                order_side=OrderSide.CLOSE,
                vix_level=None,
                attempt_number=2,
            )
            if next_limit is None:
                break
            current_limit = next_limit

        # Should stop earlier than open (tighter limit)
        assert current_limit < Decimal("1.32")

    def test_pricing_sequence_generation(self) -> None:
        """Test generation of complete pricing sequence."""
        contract = create_test_contract(bid=Decimal("1.00"), ask=Decimal("1.10"))
        pricer = MarketabilityPricer()

        result = pricer.generate_pricing_sequence(
            contract=contract,
            order_side=OrderSide.OPEN,
            vix_level=Decimal("20"),  # Calm
        )

        # Should have multiple steps
        assert result.total_attempts > 1
        assert len(result.pricing_steps) > 1

        # All steps should show increasing price
        for i in range(1, len(result.pricing_steps)):
            assert result.pricing_steps[i].limit_price > result.pricing_steps[i - 1].limit_price


class TestSlippageTracker:
    """Test slippage tracking and daily limits."""

    def test_slippage_recording(self) -> None:
        """Test that slippage is recorded correctly."""
        tracker = SlippageTracker()

        # Record a trade with acceptable slippage (< 3%)
        tracker.record_trade(
            premium_paid=Decimal("1000"),
            mid_price=Decimal("1.00"),
            slippage_amount=Decimal("20"),  # 2% slippage (20/1000)
        )

        # Check daily limit (should be under 3%)
        allowed, current_pct = tracker.check_daily_limit(Decimal("0"))
        assert allowed
        assert current_pct == Decimal("0.02")  # 20 / 1000 = 2%

    def test_daily_slippage_limit_enforcement(self) -> None:
        """Test that daily slippage limit is enforced."""
        tracker = SlippageTracker()

        # Record multiple trades approaching limit
        # Daily limit is 3% of total premium
        tracker.record_trade(
            premium_paid=Decimal("1000"),
            mid_price=Decimal("1.00"),
            slippage_amount=Decimal("20"),  # 2% slippage
        )

        # Check if another 2% slippage would be allowed
        # Total would be 4% > 3% limit
        allowed, current_pct = tracker.check_daily_limit(Decimal("20"))
        assert not allowed  # Should reject (40 / 1000 = 4% > 3%)
        assert current_pct > Decimal("0.03")

    def test_daily_reset(self) -> None:
        """Test that daily counters reset."""
        tracker = SlippageTracker()

        # Record some trades
        tracker.record_trade(
            premium_paid=Decimal("100"),
            mid_price=Decimal("1.00"),
            slippage_amount=Decimal("5"),
        )

        # Reset
        tracker.reset_daily()

        # Should be at zero after reset
        allowed, current_pct = tracker.check_daily_limit(Decimal("0"))
        assert allowed
        assert current_pct == Decimal("0")


class TestMarketSnapshots:
    """Test market snapshot recording for reproducibility."""

    def test_market_snapshot_creation(self) -> None:
        """Test creating a market snapshot."""
        snapshot = MarketSnapshot(
            option_symbol="SPY241231P00450000",
            timestamp="2024-01-15T10:30:00Z",
            bid_price=Decimal("1.00"),
            ask_price=Decimal("1.10"),
            mid_price=Decimal("1.05"),
            spread_pct=Decimal("0.0952"),  # (1.10 - 1.00) / 1.05 = 9.52%
            vix_level=Decimal("15.5"),
        )

        assert snapshot.option_symbol == "SPY241231P00450000"
        assert snapshot.bid_price == Decimal("1.00")
        assert snapshot.ask_price == Decimal("1.10")
        assert snapshot.mid_price == Decimal("1.05")

    def test_pricing_with_recorded_snapshot(self) -> None:
        """Test pricing algorithm with a recorded market snapshot."""
        # This demonstrates how to test with actual market data
        snapshot = MarketSnapshot(
            option_symbol="QQQ240315P00350000",
            timestamp="2024-01-15T14:00:00Z",
            bid_price=Decimal("2.15"),
            ask_price=Decimal("2.25"),
            mid_price=Decimal("2.20"),
            spread_pct=Decimal("0.0454"),  # ~4.5% spread
            vix_level=Decimal("18.3"),
        )

        # Create contract from snapshot
        contract = create_test_contract(
            bid=snapshot.bid_price,
            ask=snapshot.ask_price,
            symbol=snapshot.option_symbol,
        )

        pricer = MarketabilityPricer()

        # Test pricing sequence
        result = pricer.generate_pricing_sequence(
            contract=contract,
            order_side=OrderSide.OPEN,
            vix_level=snapshot.vix_level,
        )

        # Initial price should be at mid
        assert result.pricing_steps[0].limit_price == snapshot.mid_price

        # Should step toward ask
        assert result.pricing_steps[-1].limit_price > snapshot.mid_price
        assert result.pricing_steps[-1].limit_price <= snapshot.ask_price
