"""
Unit tests for trading math calculations.

Tests price calculations, rounding, position sizing, and portfolio math
to ensure accuracy and handle edge cases.
"""

from decimal import ROUND_HALF_UP, Decimal, getcontext

# Set high precision for Decimal calculations
getcontext().prec = 28


class TestPriceRounding:
    """Test price rounding to tick sizes."""

    def test_round_to_penny(self):
        """Test rounding to penny (0.01 tick size)."""
        # Standard stock tick size
        tick_size = Decimal("0.01")

        test_cases = [
            (Decimal("100.123"), Decimal("100.12")),
            (Decimal("100.126"), Decimal("100.13")),
            (Decimal("100.125"), Decimal("100.13")),  # Round half up
            (Decimal("100.124"), Decimal("100.12")),
        ]

        for input_price, expected in test_cases:
            rounded = round_to_tick_size(input_price, tick_size)
            assert rounded == expected, f"Expected {expected}, got {rounded}"

    def test_round_to_nickel(self):
        """Test rounding to nickel (0.05 tick size)."""
        # Some ETFs trade in nickel increments
        tick_size = Decimal("0.05")

        test_cases = [
            (Decimal("100.12"), Decimal("100.10")),
            (Decimal("100.13"), Decimal("100.15")),
            (Decimal("100.17"), Decimal("100.15")),
            (Decimal("100.18"), Decimal("100.20")),
        ]

        for input_price, expected in test_cases:
            rounded = round_to_tick_size(input_price, tick_size)
            assert rounded == expected, f"Expected {expected}, got {rounded}"

    def test_round_to_dollar(self):
        """Test rounding to dollar (1.00 tick size)."""
        # Some high-priced stocks
        tick_size = Decimal("1.00")

        test_cases = [
            (Decimal("1234.56"), Decimal("1235.00")),
            (Decimal("1234.49"), Decimal("1234.00")),
            (Decimal("1234.50"), Decimal("1235.00")),  # Round half up
        ]

        for input_price, expected in test_cases:
            rounded = round_to_tick_size(input_price, tick_size)
            assert rounded == expected, f"Expected {expected}, got {rounded}"

    def test_round_crypto_precision(self):
        """Test rounding for crypto with high precision."""
        # Bitcoin with 8 decimal places
        tick_size = Decimal("0.00000001")

        price = Decimal("50000.123456789")
        rounded = round_to_tick_size(price, tick_size)
        expected = Decimal("50000.12345679")

        assert rounded == expected

    def test_round_edge_cases(self):
        """Test edge cases in price rounding."""
        tick_size = Decimal("0.01")

        # Zero price
        assert round_to_tick_size(Decimal("0.00"), tick_size) == Decimal("0.00")

        # Very small price
        small_price = Decimal("0.001")
        rounded = round_to_tick_size(small_price, tick_size)
        assert rounded == Decimal("0.00")

        # Large price
        large_price = Decimal("999999.999")
        rounded = round_to_tick_size(large_price, tick_size)
        assert rounded == Decimal("1000000.00")


class TestPositionSizing:
    """Test position sizing calculations."""

    def test_calculate_shares_from_dollar_amount(self):
        """Test calculating shares from dollar allocation."""
        portfolio_value = Decimal("100000.00")
        allocation_pct = Decimal("0.10")  # 10%
        share_price = Decimal("150.00")

        dollar_amount = portfolio_value * allocation_pct
        shares = calculate_shares_from_dollars(dollar_amount, share_price)

        expected_shares = dollar_amount / share_price
        assert shares == expected_shares
        # Check precision is maintained (28 decimal places in our context)
        assert abs(shares - Decimal("66.66666666666666666666666667")) < Decimal("1E-26")

    def test_calculate_shares_rounded_down(self):
        """Test shares calculation rounded down to whole shares."""
        dollar_amount = Decimal("10000.00")
        share_price = Decimal("333.33")

        shares = calculate_shares_from_dollars(dollar_amount, share_price, round_down=True)
        expected_shares = int(dollar_amount / share_price)

        assert shares == expected_shares
        assert shares == 30  # Floor of 30.0003...

    def test_fractional_share_support(self):
        """Test fractional share calculations."""
        dollar_amount = Decimal("1000.00")
        share_price = Decimal("333.33")

        # Allow fractional shares
        shares = calculate_shares_from_dollars(dollar_amount, share_price, round_down=False)
        expected_shares = dollar_amount / share_price

        assert shares == expected_shares
        # Should be approximately 3.0003 shares
        assert abs(shares - Decimal("3.000030000300003")) < Decimal("0.000001")

    def test_position_sizing_edge_cases(self):
        """Test edge cases in position sizing."""
        # Zero dollar amount
        shares = calculate_shares_from_dollars(Decimal("0.00"), Decimal("100.00"))
        assert shares == Decimal("0.00")

        # Very small allocation
        shares = calculate_shares_from_dollars(Decimal("0.01"), Decimal("100.00"))
        assert shares == Decimal("0.0001")

        # High-priced stock with small allocation
        shares = calculate_shares_from_dollars(Decimal("100.00"), Decimal("5000.00"))
        assert shares == Decimal("0.02")


class TestPortfolioMath:
    """Test portfolio-level calculations."""

    def test_portfolio_allocation_validation(self):
        """Test portfolio allocation sums to 100%."""
        allocations = {
            "AAPL": Decimal("0.25"),
            "GOOGL": Decimal("0.25"),
            "MSFT": Decimal("0.25"),
            "CASH": Decimal("0.25"),
        }

        total_allocation = sum(allocations.values())
        assert total_allocation == Decimal("1.00")

        # Test with rounding errors
        allocations_with_rounding = {
            "AAPL": Decimal("0.333333"),
            "GOOGL": Decimal("0.333333"),
            "MSFT": Decimal("0.333334"),
        }

        total_with_rounding = sum(allocations_with_rounding.values())
        assert abs(total_with_rounding - Decimal("1.00")) == Decimal("0.00")

    def test_portfolio_value_calculation(self):
        """Test total portfolio value calculation."""
        positions = {
            "AAPL": {"shares": Decimal("100"), "current_price": Decimal("150.00")},
            "GOOGL": {"shares": Decimal("50"), "current_price": Decimal("2800.00")},
        }
        cash = Decimal("10000.00")

        total_equity_value = sum(pos["shares"] * pos["current_price"] for pos in positions.values())
        total_portfolio_value = total_equity_value + cash

        expected_equity = Decimal("100") * Decimal("150.00") + Decimal("50") * Decimal("2800.00")
        expected_total = expected_equity + cash

        assert total_equity_value == expected_equity
        assert total_portfolio_value == expected_total
        assert total_portfolio_value == Decimal("165000.00")

    def test_rebalancing_calculations(self):
        """Test portfolio rebalancing calculations."""
        current_portfolio_value = Decimal("100000.00")
        target_allocations = {
            "AAPL": Decimal("0.50"),
            "GOOGL": Decimal("0.30"),
            "CASH": Decimal("0.20"),
        }

        current_positions = {
            "AAPL": {"market_value": Decimal("40000.00"), "current_price": Decimal("150.00")},
            "GOOGL": {"market_value": Decimal("20000.00"), "current_price": Decimal("2800.00")},
        }
        current_cash = Decimal("40000.00")

        # Calculate target dollar amounts
        target_dollars = {
            symbol: current_portfolio_value * allocation
            for symbol, allocation in target_allocations.items()
        }

        # Calculate rebalancing needs
        rebalancing_needs = {}
        for symbol in target_allocations:
            if symbol == "CASH":
                current_value = current_cash
            else:
                current_value = current_positions[symbol]["market_value"]

            target_value = target_dollars[symbol]
            rebalancing_needs[symbol] = target_value - current_value

        # AAPL should need +$10,000 (50% of 100k = 50k, currently 40k)
        assert rebalancing_needs["AAPL"] == Decimal("10000.00")

        # GOOGL should need +$10,000 (30% of 100k = 30k, currently 20k)
        assert rebalancing_needs["GOOGL"] == Decimal("10000.00")

        # CASH should need -$20,000 (20% of 100k = 20k, currently 40k)
        assert rebalancing_needs["CASH"] == Decimal("-20000.00")

        # Total rebalancing should sum to zero
        assert sum(rebalancing_needs.values()) == Decimal("0.00")

    def test_profit_loss_calculations(self):
        """Test P&L calculations."""
        # Realized P&L
        buy_price = Decimal("100.00")
        sell_price = Decimal("110.00")
        shares = Decimal("100")

        realized_pnl = (sell_price - buy_price) * shares
        assert realized_pnl == Decimal("1000.00")

        # Unrealized P&L
        current_price = Decimal("105.00")
        unrealized_pnl = (current_price - buy_price) * shares
        assert unrealized_pnl == Decimal("500.00")

        # Percentage returns
        pct_return = (current_price - buy_price) / buy_price
        assert pct_return == Decimal("0.05")  # 5%

    def test_compound_returns(self):
        """Test compound return calculations."""
        initial_value = Decimal("100000.00")

        # Daily returns
        daily_returns = [
            Decimal("0.01"),  # +1%
            Decimal("-0.005"),  # -0.5%
            Decimal("0.02"),  # +2%
            Decimal("0.00"),  # 0%
            Decimal("-0.01"),  # -1%
        ]

        # Calculate compound return
        compound_factor = Decimal("1.00")
        for daily_return in daily_returns:
            compound_factor *= Decimal("1.00") + daily_return

        initial_value * compound_factor
        compound_factor - Decimal("1.00")

        # Verify calculation
        expected_factor = (
            Decimal("1.01") * Decimal("0.995") * Decimal("1.02") * Decimal("1.00") * Decimal("0.99")
        )

        assert abs(compound_factor - expected_factor) < Decimal("1E-10")


class TestPrecisionHandling:
    """Test decimal precision and rounding edge cases."""

    def test_decimal_precision_maintenance(self):
        """Test that Decimal precision is maintained in calculations."""
        # High precision calculation
        a = Decimal("100.123456789012345")
        b = Decimal("200.987654321098765")

        result = a + b
        expected = Decimal("301.11111111011111")

        assert result == expected

        # Multiplication with precision
        result_mult = a * b
        # Should maintain precision according to Decimal context
        assert isinstance(result_mult, Decimal)

    def test_floating_point_conversion_accuracy(self):
        """Test accuracy when converting between float and Decimal."""
        # Test cases where float precision matters
        float_value = 0.1 + 0.2  # Famous floating point issue
        decimal_value = Decimal("0.1") + Decimal("0.2")

        # Decimal should be exact
        assert decimal_value == Decimal("0.3")

        # Float should have precision issues
        assert float_value != 0.3

        # Converting float to Decimal preserves the imprecision
        decimal_from_float = Decimal(str(float_value))
        assert decimal_from_float != Decimal("0.3")

    def test_rounding_modes(self):
        """Test different rounding modes."""
        value = Decimal("2.5")

        # Round half up (default for trading)
        rounded_up = value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert rounded_up == Decimal("3")

        # Test with negative values
        negative_value = Decimal("-2.5")
        rounded_neg = negative_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert rounded_neg == Decimal(
            "-3"
        )  # Round half up means away from zero for negative numbers


# Helper functions that would be implemented in the main codebase
def round_to_tick_size(price: Decimal, tick_size: Decimal) -> Decimal:
    """Round price to the nearest tick size."""
    return (price / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick_size


def calculate_shares_from_dollars(
    dollar_amount: Decimal, share_price: Decimal, round_down: bool = False
) -> Decimal:
    """Calculate number of shares from dollar amount."""
    shares = dollar_amount / share_price

    if round_down:
        # Round down to whole shares
        return Decimal(int(shares))
    else:
        # Return exact fractional shares
        return shares


class TestHelperFunctions:
    """Test the helper functions defined in this module."""

    def test_round_to_tick_size_function(self):
        """Test our tick size rounding function."""
        assert round_to_tick_size(Decimal("100.123"), Decimal("0.01")) == Decimal("100.12")
        assert round_to_tick_size(Decimal("100.126"), Decimal("0.01")) == Decimal("100.13")

    def test_calculate_shares_function(self):
        """Test our shares calculation function."""
        shares = calculate_shares_from_dollars(Decimal("1000"), Decimal("100"))
        assert shares == Decimal("10")

        shares_rounded = calculate_shares_from_dollars(
            Decimal("1000"), Decimal("333.33"), round_down=True
        )
        assert shares_rounded == Decimal("3")
