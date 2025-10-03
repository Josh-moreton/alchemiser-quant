"""Business Unit: shared | Status: current.

Comprehensive unit and property-based tests for Money value object.

Tests Money value object operations with Decimal arithmetic to avoid
float precision errors per project guardrails.
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP
from hypothesis import given, strategies as st, assume

from the_alchemiser.shared.types.money import Money


class TestMoneyConstruction:
    """Test Money value object construction and validation."""

    @pytest.mark.unit
    def test_create_valid_money_usd(self):
        """Test creating valid Money object with USD."""
        m = Money(Decimal("100.50"), "USD")
        assert m.amount == Decimal("100.50")
        assert m.currency == "USD"

    @pytest.mark.unit
    def test_create_valid_money_eur(self):
        """Test creating valid Money object with EUR."""
        m = Money(Decimal("50.25"), "EUR")
        assert m.amount == Decimal("50.25")
        assert m.currency == "EUR"

    @pytest.mark.unit
    def test_amount_normalized_to_two_decimals(self):
        """Test that amount is normalized to 2 decimal places."""
        m = Money(Decimal("100.123"), "USD")
        assert m.amount == Decimal("100.12")

    @pytest.mark.unit
    def test_amount_rounding_half_up(self):
        """Test that amount uses ROUND_HALF_UP."""
        m = Money(Decimal("100.125"), "USD")
        assert m.amount == Decimal("100.13")
        
        m2 = Money(Decimal("100.124"), "USD")
        assert m2.amount == Decimal("100.12")

    @pytest.mark.unit
    def test_zero_amount(self):
        """Test creating Money with zero amount."""
        m = Money(Decimal("0.00"), "USD")
        assert m.amount == Decimal("0.00")
        assert m.currency == "USD"

    @pytest.mark.unit
    def test_negative_amount_raises_value_error(self):
        """Test that negative amounts raise ValueError."""
        with pytest.raises(ValueError, match="Money amount cannot be negative"):
            Money(Decimal("-1.00"), "USD")

    @pytest.mark.unit
    def test_negative_small_amount_raises_value_error(self):
        """Test that small negative amounts raise ValueError."""
        with pytest.raises(ValueError, match="Money amount cannot be negative"):
            Money(Decimal("-0.01"), "USD")

    @pytest.mark.unit
    def test_invalid_currency_code_too_short(self):
        """Test that currency codes must be 3 characters."""
        with pytest.raises(ValueError, match="Currency must be ISO 4217 code"):
            Money(Decimal("100.00"), "US")

    @pytest.mark.unit
    def test_invalid_currency_code_too_long(self):
        """Test that currency codes must be 3 characters."""
        with pytest.raises(ValueError, match="Currency must be ISO 4217 code"):
            Money(Decimal("100.00"), "USDD")

    @pytest.mark.unit
    def test_valid_three_letter_currency(self):
        """Test various valid 3-letter currency codes."""
        currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD"]
        for curr in currencies:
            m = Money(Decimal("100.00"), curr)
            assert m.currency == curr

    @pytest.mark.unit
    def test_money_is_frozen(self):
        """Test that Money is immutable (frozen dataclass)."""
        m = Money(Decimal("100.00"), "USD")
        with pytest.raises(AttributeError):
            m.amount = Decimal("200.00")


class TestMoneyAddition:
    """Test Money addition operations."""

    @pytest.mark.unit
    def test_add_same_currency(self):
        """Test adding two Money objects with same currency."""
        m1 = Money(Decimal("100.50"), "USD")
        m2 = Money(Decimal("50.25"), "USD")
        result = m1.add(m2)
        
        assert result.amount == Decimal("150.75")
        assert result.currency == "USD"

    @pytest.mark.unit
    def test_add_preserves_precision(self):
        """Test that addition maintains 2 decimal precision."""
        m1 = Money(Decimal("100.11"), "USD")
        m2 = Money(Decimal("50.22"), "USD")
        result = m1.add(m2)
        
        assert result.amount == Decimal("150.33")

    @pytest.mark.unit
    def test_add_zero_amount(self):
        """Test adding zero amount."""
        m1 = Money(Decimal("100.00"), "USD")
        m2 = Money(Decimal("0.00"), "USD")
        result = m1.add(m2)
        
        assert result.amount == Decimal("100.00")
        assert result.currency == "USD"

    @pytest.mark.unit
    def test_add_different_currencies_raises_value_error(self):
        """Test that adding different currencies raises ValueError."""
        m1 = Money(Decimal("100.00"), "USD")
        m2 = Money(Decimal("50.00"), "EUR")
        
        with pytest.raises(ValueError, match="Cannot add different currencies"):
            m1.add(m2)

    @pytest.mark.unit
    def test_add_returns_new_object(self):
        """Test that addition returns a new Money object."""
        m1 = Money(Decimal("100.00"), "USD")
        m2 = Money(Decimal("50.00"), "USD")
        result = m1.add(m2)
        
        # Original objects unchanged
        assert m1.amount == Decimal("100.00")
        assert m2.amount == Decimal("50.00")
        # Result is new object
        assert result is not m1
        assert result is not m2


class TestMoneyMultiplication:
    """Test Money multiplication operations."""

    @pytest.mark.unit
    def test_multiply_by_integer_factor(self):
        """Test multiplying Money by an integer Decimal."""
        m = Money(Decimal("100.00"), "USD")
        result = m.multiply(Decimal("2"))
        
        assert result.amount == Decimal("200.00")
        assert result.currency == "USD"

    @pytest.mark.unit
    def test_multiply_by_decimal_factor(self):
        """Test multiplying Money by a decimal factor."""
        m = Money(Decimal("100.00"), "USD")
        result = m.multiply(Decimal("1.5"))
        
        assert result.amount == Decimal("150.00")
        assert result.currency == "USD"

    @pytest.mark.unit
    def test_multiply_by_fractional_factor(self):
        """Test multiplying by a fraction."""
        m = Money(Decimal("100.00"), "USD")
        result = m.multiply(Decimal("0.25"))
        
        assert result.amount == Decimal("25.00")
        assert result.currency == "USD"

    @pytest.mark.unit
    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        m = Money(Decimal("100.00"), "USD")
        result = m.multiply(Decimal("0"))
        
        assert result.amount == Decimal("0.00")
        assert result.currency == "USD"

    @pytest.mark.unit
    def test_multiply_by_one(self):
        """Test multiplying by one (identity)."""
        m = Money(Decimal("100.50"), "USD")
        result = m.multiply(Decimal("1"))
        
        assert result.amount == Decimal("100.50")
        assert result.currency == "USD"

    @pytest.mark.unit
    def test_multiply_preserves_precision(self):
        """Test that multiplication result is rounded to 2 decimals."""
        m = Money(Decimal("10.00"), "USD")
        result = m.multiply(Decimal("0.333"))
        
        # 10.00 * 0.333 = 3.330, rounded to 3.33
        assert result.amount == Decimal("3.33")

    @pytest.mark.unit
    def test_multiply_with_rounding(self):
        """Test multiplication with ROUND_HALF_UP rounding."""
        m = Money(Decimal("10.00"), "USD")
        result = m.multiply(Decimal("0.335"))
        
        # 10.00 * 0.335 = 3.350, rounds up to 3.35
        assert result.amount == Decimal("3.35")

    @pytest.mark.unit
    def test_multiply_returns_new_object(self):
        """Test that multiplication returns a new Money object."""
        m = Money(Decimal("100.00"), "USD")
        result = m.multiply(Decimal("2"))
        
        # Original unchanged
        assert m.amount == Decimal("100.00")
        # Result is new object
        assert result is not m


# Property-based tests using Hypothesis
class TestMoneyProperties:
    """Property-based tests for Money value object."""

    @pytest.mark.property
    @given(
        st.decimals(min_value="0", max_value="1000000", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_construction_preserves_non_negative(self, amount):
        """Property: constructed Money should always be non-negative."""
        m = Money(amount, "USD")
        assert m.amount >= 0

    @pytest.mark.property
    @given(
        st.decimals(min_value="0", max_value="1000000", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_amount_precision_is_two_decimals(self, amount):
        """Property: Money amount should always have at most 2 decimal places."""
        m = Money(amount, "USD")
        # Check that the amount has at most 2 decimal places
        quantized = m.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert m.amount == quantized

    @pytest.mark.property
    @given(
        st.decimals(min_value="0.01", max_value="100000", allow_nan=False, allow_infinity=False, places=2),
        st.decimals(min_value="0.01", max_value="100000", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_addition_commutative(self, amount1, amount2):
        """Property: addition should be commutative (a + b = b + a)."""
        m1 = Money(amount1, "USD")
        m2 = Money(amount2, "USD")
        
        result1 = m1.add(m2)
        result2 = m2.add(m1)
        
        assert result1.amount == result2.amount

    @pytest.mark.property
    @given(
        st.decimals(min_value="0.01", max_value="10000", allow_nan=False, allow_infinity=False, places=2),
        st.decimals(min_value="0.01", max_value="10000", allow_nan=False, allow_infinity=False, places=2),
        st.decimals(min_value="0.01", max_value="10000", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_addition_associative(self, amount1, amount2, amount3):
        """Property: addition should be associative ((a + b) + c = a + (b + c))."""
        m1 = Money(amount1, "USD")
        m2 = Money(amount2, "USD")
        m3 = Money(amount3, "USD")
        
        result1 = m1.add(m2).add(m3)
        result2 = m1.add(m2.add(m3))
        
        assert result1.amount == result2.amount

    @pytest.mark.property
    @given(
        st.decimals(min_value="0.01", max_value="100000", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_addition_identity(self, amount):
        """Property: adding zero should not change the amount."""
        m = Money(amount, "USD")
        zero = Money(Decimal("0.00"), "USD")
        
        result = m.add(zero)
        
        assert result.amount == m.amount

    @pytest.mark.property
    @given(
        st.decimals(min_value="0.01", max_value="100000", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_multiplication_identity(self, amount):
        """Property: multiplying by one should not change the amount."""
        m = Money(amount, "USD")
        result = m.multiply(Decimal("1"))
        
        assert result.amount == m.amount

    @pytest.mark.property
    @given(
        st.decimals(min_value="0.01", max_value="100000", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_multiplication_zero(self, amount):
        """Property: multiplying by zero should give zero."""
        m = Money(amount, "USD")
        result = m.multiply(Decimal("0"))
        
        assert result.amount == Decimal("0.00")

    @pytest.mark.property
    @given(
        st.decimals(min_value="1.00", max_value="10000", allow_nan=False, allow_infinity=False, places=2),
        st.decimals(min_value="0.01", max_value="10", allow_nan=False, allow_infinity=False, places=2),
        st.decimals(min_value="0.01", max_value="10", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_multiplication_associative(self, amount, factor1, factor2):
        """Property: multiplication should be associative ((a * b) * c = a * (b * c))."""
        m = Money(amount, "USD")
        
        result1 = m.multiply(factor1).multiply(factor2)
        result2 = m.multiply(factor1 * factor2)
        
        # Account for potential rounding differences with chained multiplication
        # Allow up to 2 cents difference due to intermediate rounding
        assert abs(result1.amount - result2.amount) <= Decimal("0.02")

    @pytest.mark.property
    @given(
        st.decimals(min_value="0.01", max_value="10000", allow_nan=False, allow_infinity=False, places=2),
        st.decimals(min_value="0.01", max_value="100", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_multiply_result_non_negative(self, amount, factor):
        """Property: multiplying non-negative amounts should give non-negative result."""
        assume(factor >= 0)
        m = Money(amount, "USD")
        result = m.multiply(factor)
        
        assert result.amount >= 0

    @pytest.mark.property
    @given(
        st.decimals(min_value="0.10", max_value="10000", allow_nan=False, allow_infinity=False, places=2),
        st.decimals(min_value="1.10", max_value="100", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_multiply_increases_with_factor_greater_than_one(self, amount, factor):
        """Property: multiplying by factor > 1 should increase amount."""
        # Ensure minimum amount is enough that rounding won't cause issues
        assume(amount >= Decimal("0.10"))
        m = Money(amount, "USD")
        result = m.multiply(factor)
        
        assert result.amount > m.amount

    @pytest.mark.property
    @given(
        st.decimals(min_value="1.00", max_value="10000", allow_nan=False, allow_infinity=False, places=2),
        st.decimals(min_value="0.01", max_value="0.99", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_multiply_decreases_with_factor_less_than_one(self, amount, factor):
        """Property: multiplying by factor < 1 should decrease amount."""
        m = Money(amount, "USD")
        result = m.multiply(factor)
        
        assert result.amount < m.amount
