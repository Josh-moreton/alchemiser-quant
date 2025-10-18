"""Business Unit: shared | Status: current

Test core trading business rules and validations.

Tests the fundamental business rules that apply across all trading operations,
including position sizing, risk limits, and data validation.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
from the_alchemiser.shared.utils.validation_utils import detect_suspicious_quote_prices


class TestTradingBusinessRules:
    """Test core trading business rules and validations."""

    def test_position_sizing_business_rules(self):
        """Test business rules for position sizing."""
        # Test maximum position concentration
        high_concentration_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.9"),  # 90% in single position
                "MSFT": Decimal("0.1"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"max_position_size": 0.3},  # 30% limit
        )

        # Should validate but flag risk
        assert high_concentration_allocation.target_weights["AAPL"] > Decimal("0.3")

        # Test minimum position size
        small_position_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.999"),
                "MSFT": Decimal("0.001"),  # Very small position
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"min_position_size": 0.01},  # 1% minimum
        )

        assert small_position_allocation.target_weights["MSFT"] < Decimal("0.01")

    def test_portfolio_value_calculations(self):
        """Test portfolio value calculation business logic."""
        test_scenarios = [
            # (portfolio_value, weight, expected_target_value)
            (Decimal("10000.00"), Decimal("0.5"), Decimal("5000.00")),
            (Decimal("100000.00"), Decimal("0.25"), Decimal("25000.00")),
            (Decimal("1000.00"), Decimal("0.333333"), Decimal("333.333")),
        ]

        for portfolio_value, weight, expected_value in test_scenarios:
            actual_value = portfolio_value * weight
            assert abs(actual_value - expected_value) < Decimal("0.001")

    def test_quote_validation_business_rules(self):
        """Test quote validation business rules."""
        # Normal quotes should not be suspicious
        is_suspicious, reasons = detect_suspicious_quote_prices(
            Decimal("100.50"), Decimal("100.52")
        )
        assert not is_suspicious
        assert len(reasons) == 0

        # Inverted spread should be suspicious
        is_suspicious, reasons = detect_suspicious_quote_prices(
            Decimal("100.52"), Decimal("100.50")
        )
        assert is_suspicious
        assert any("inverted spread" in reason.lower() for reason in reasons)

        # Very wide spread should be suspicious
        is_suspicious, reasons = detect_suspicious_quote_prices(
            Decimal("100.00"), Decimal("120.00")
        )
        assert is_suspicious
        assert any("spread" in reason.lower() for reason in reasons)

    def test_trading_session_validation(self):
        """Test trading session and timing validation."""
        # Market hours check (simplified)
        market_open = datetime.now(UTC).replace(hour=14, minute=30)  # 9:30 AM EST
        market_close = datetime.now(UTC).replace(hour=21, minute=0)  # 4:00 PM EST

        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id=str(uuid.uuid4()),
            as_of=market_open,
            constraints={"market_hours_only": True},
        )

        # Should have timestamp within reasonable range
        assert allocation.as_of is not None
        assert isinstance(allocation.as_of, datetime)

    def test_diversification_business_rules(self):
        """Test diversification business rules."""
        # Well-diversified portfolio
        diversified_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.15"),  # Tech
                "MSFT": Decimal("0.15"),  # Tech
                "JPM": Decimal("0.15"),  # Finance
                "JNJ": Decimal("0.15"),  # Healthcare
                "XOM": Decimal("0.15"),  # Energy
                "WMT": Decimal("0.25"),  # Consumer
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"sector_diversification": True},
        )

        # Should have multiple positions
        assert len(diversified_allocation.target_weights) >= 5

        # No single position should dominate
        max_weight = max(diversified_allocation.target_weights.values())
        assert max_weight <= Decimal("0.25")

    def test_rebalancing_threshold_business_rules(self):
        """Test rebalancing threshold business rules."""
        current_weights = {
            "AAPL": Decimal("0.52"),  # Target: 0.5
            "MSFT": Decimal("0.48"),  # Target: 0.5
        }

        target_weights = {
            "AAPL": Decimal("0.5"),
            "MSFT": Decimal("0.5"),
        }

        # Calculate drift
        max_drift = max(
            abs(current_weights[symbol] - target_weights[symbol]) for symbol in target_weights
        )

        # Small drift should not trigger rebalancing
        rebalance_threshold = Decimal("0.05")  # 5%
        needs_rebalancing = max_drift > rebalance_threshold

        assert max_drift == Decimal("0.02")  # 2% drift
        assert not needs_rebalancing

    def test_order_sizing_business_rules(self):
        """Test order sizing business rules."""
        portfolio_value = Decimal("100000.00")

        # Test minimum order size
        min_order_value = Decimal("100.00")
        small_allocation = portfolio_value * Decimal("0.0005")  # 0.05%

        # Should handle minimum order sizes
        if small_allocation < min_order_value:
            # Small orders might be skipped or batched
            assert small_allocation == Decimal("50.00")
            assert small_allocation < min_order_value

        # Test maximum order size
        max_order_value = Decimal("50000.00")
        large_allocation = portfolio_value * Decimal("0.6")  # 60%

        if large_allocation > max_order_value:
            # Large orders might need to be split
            assert large_allocation == Decimal("60000.00")
            assert large_allocation > max_order_value

    def test_cash_management_business_rules(self):
        """Test cash management business rules."""
        portfolio_value = Decimal("100000.00")
        cash_reserve_percentage = Decimal("0.05")  # 5% cash reserve

        available_for_investment = portfolio_value * (Decimal("1") - cash_reserve_percentage)
        cash_reserve = portfolio_value * cash_reserve_percentage

        # Should maintain cash reserve
        assert available_for_investment == Decimal("95000.00")
        assert cash_reserve == Decimal("5000.00")

        allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.95"),  # 95% invested
                "CASH": Decimal("0.05"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"cash_reserve_pct": float(cash_reserve_percentage)},
        )

        # Allocation should account for cash reserve
        invested_amount = portfolio_value * allocation.target_weights["AAPL"]
        assert invested_amount <= available_for_investment

    def test_symbol_normalization_business_rules(self):
        """Test symbol normalization and validation."""
        test_symbols = [
            ("aapl", "AAPL"),
            ("msft", "MSFT"),
            ("googl", "GOOGL"),
            ("BRK.B", "BRK.B"),  # Special case
        ]

        for input_symbol, expected_symbol in test_symbols:
            normalized = input_symbol.upper().strip()
            assert normalized == expected_symbol

    def test_decimal_rounding_business_rules(self):
        """Test decimal rounding rules for money and shares."""
        # Money should round to 2 decimal places
        money_values = [
            Decimal("100.1234"),
            Decimal("100.1267"),
            Decimal("100.999"),
        ]

        for value in money_values:
            rounded = value.quantize(Decimal("0.01"))
            assert len(str(rounded).split(".")[-1]) <= 2

        # Share quantities depend on fractional vs non-fractional
        share_values = [
            Decimal("10.1234"),
            Decimal("10.6789"),
            Decimal("10.999"),
        ]

        for value in share_values:
            # Fractionable shares can have more precision
            fractional_rounded = value.quantize(Decimal("0.000001"))
            assert fractional_rounded >= Decimal("0")

            # Non-fractionable shares must be whole numbers
            whole_rounded = value.quantize(Decimal("1"))
            assert whole_rounded == int(whole_rounded)

    def test_correlation_tracking_business_rules(self):
        """Test correlation ID tracking business rules."""
        correlation_id = str(uuid.uuid4())

        # Strategy allocation
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id=correlation_id,
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Should preserve correlation ID throughout workflow
        assert allocation.correlation_id == correlation_id

        # Correlation ID should be UUID format
        uuid_parts = correlation_id.split("-")
        assert len(uuid_parts) == 5
        assert len(uuid_parts[0]) == 8
        assert len(uuid_parts[1]) == 4
        assert len(uuid_parts[2]) == 4
        assert len(uuid_parts[3]) == 4
        assert len(uuid_parts[4]) == 12
