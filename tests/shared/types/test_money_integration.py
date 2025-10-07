"""Business Unit: shared | Status: current.

Integration tests demonstrating Money adoption in portfolio calculations.

These tests validate that Money is properly used for monetary calculations
across portfolio and P&L computations, ensuring type safety and precision.
"""

import pytest
from decimal import Decimal

from the_alchemiser.shared.types.money import Money
from the_alchemiser.shared.utils.portfolio_calculations import build_allocation_comparison


class TestMoneyIntegration:
    """Integration tests for Money usage in portfolio calculations."""

    @pytest.mark.integration
    def test_portfolio_calculation_uses_money_precision(self):
        """Test that portfolio calculations maintain Money-level precision."""
        # Setup: Portfolio with precise allocations
        consolidated_portfolio = {
            "AAPL": 0.333333,  # 33.3333%
            "MSFT": 0.333333,  # 33.3333%
            "GOOGL": 0.333334,  # 33.3334% (ensures sum = 1.0)
        }
        account_dict = {
            "portfolio_value": 10000.00,
            "equity": 10000.00,
        }
        positions_dict = {}

        # Execute
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )

        # Verify: Target values should have Money-level precision (2 decimals)
        target_values = result["target_values"]
        for symbol, value in target_values.items():
            assert isinstance(value, Decimal)
            # Check that values are rounded to 2 decimal places (Money standard)
            assert value == value.quantize(Decimal("0.01"))

    @pytest.mark.integration
    def test_money_prevents_negative_amounts(self):
        """Test that Money type prevents negative monetary values."""
        # Money should raise NegativeMoneyError for negative amounts
        from the_alchemiser.shared.types.money import NegativeMoneyError

        with pytest.raises(NegativeMoneyError):
            Money(Decimal("-100.00"), "USD")

    @pytest.mark.integration
    def test_money_currency_awareness(self):
        """Test that Money enforces currency consistency."""
        from the_alchemiser.shared.types.money import CurrencyMismatchError

        usd_money = Money(Decimal("100.00"), "USD")
        eur_money = Money(Decimal("50.00"), "EUR")

        # Should raise error when mixing currencies
        with pytest.raises(CurrencyMismatchError):
            usd_money.add(eur_money)

    @pytest.mark.integration
    def test_money_boundary_conversion(self):
        """Test Money conversion at boundaries (DTO ↔ Money)."""
        # Convert from Decimal (DTO) to Money (business logic)
        dto_amount = Decimal("100.50")
        money = Money.from_decimal(dto_amount, "USD")
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"

        # Convert back to Decimal (for DTO)
        result_decimal = money.to_decimal()
        assert result_decimal == dto_amount
        assert isinstance(result_decimal, Decimal)

    @pytest.mark.integration
    def test_portfolio_delta_calculation_with_money(self):
        """Test that portfolio deltas are calculated using Money precision."""
        consolidated_portfolio = {"AAPL": 0.5, "MSFT": 0.5}
        account_dict = {"portfolio_value": 10000.00}
        positions_dict = {"AAPL": 4000.00, "MSFT": 5000.00}

        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )

        # Verify deltas maintain precision
        deltas = result["deltas"]
        assert isinstance(deltas["AAPL"], Decimal)
        assert isinstance(deltas["MSFT"], Decimal)

        # Check precision (2 decimal places)
        for delta in deltas.values():
            assert delta == delta.quantize(Decimal("0.01"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
