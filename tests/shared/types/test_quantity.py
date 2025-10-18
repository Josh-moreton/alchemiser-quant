"""Business Unit: shared | Status: current.

Comprehensive unit and property-based tests for Quantity value object.

Tests Quantity value object validation with Decimal arithmetic per guardrails.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.types.quantity import Quantity


class TestQuantityConstruction:
    """Test Quantity value object construction and validation."""

    @pytest.mark.unit
    def test_create_valid_quantity_one(self):
        """Test creating Quantity with value 1."""
        q = Quantity(Decimal("1"))
        assert q.value == Decimal("1")

    @pytest.mark.unit
    def test_create_valid_quantity_ten(self):
        """Test creating Quantity with value 10."""
        q = Quantity(Decimal("10"))
        assert q.value == Decimal("10")

    @pytest.mark.unit
    def test_create_valid_quantity_large(self):
        """Test creating Quantity with large value."""
        q = Quantity(Decimal("1000"))
        assert q.value == Decimal("1000")

    @pytest.mark.unit
    def test_create_quantity_zero(self):
        """Test creating Quantity with value 0."""
        q = Quantity(Decimal("0"))
        assert q.value == Decimal("0")

    @pytest.mark.unit
    def test_negative_quantity_raises_value_error(self):
        """Test that negative quantities raise ValueError."""
        with pytest.raises(ValueError):
            Quantity(Decimal("-1"))

    @pytest.mark.unit
    def test_fractional_quantity_raises_value_error(self):
        """Test that fractional quantities raise ValueError."""
        with pytest.raises(ValueError):
            Quantity(Decimal("1.5"))

    @pytest.mark.unit
    def test_small_fractional_quantity_raises_value_error(self):
        """Test that small fractional quantities raise ValueError."""
        with pytest.raises(ValueError):
            Quantity(Decimal("0.1"))

    @pytest.mark.unit
    def test_quantity_is_frozen(self):
        """Test that Quantity is immutable (frozen dataclass)."""
        q = Quantity(Decimal("10"))
        with pytest.raises(AttributeError):
            q.value = Decimal("20")


# Property-based tests using Hypothesis
class TestQuantityProperties:
    """Property-based tests for Quantity value object."""

    @pytest.mark.property
    @given(st.integers(min_value=0, max_value=1000000))
    def test_non_negative_integers_valid(self, value):
        """Property: all non-negative integers should be valid Quantity."""
        q = Quantity(Decimal(str(value)))
        assert q.value == Decimal(str(value))

    @pytest.mark.property
    @given(st.integers(min_value=-1000000, max_value=-1))
    def test_negative_integers_invalid(self, value):
        """Property: all negative integers should be invalid Quantity."""
        with pytest.raises(ValueError):
            Quantity(Decimal(str(value)))

    @pytest.mark.property
    @given(
        st.decimals(
            min_value="0.01", max_value="1000000", allow_nan=False, allow_infinity=False, places=2
        )
    )
    def test_fractional_values_invalid(self, value):
        """Property: all fractional values should be invalid Quantity."""
        # Only test values that are actually fractional
        if value != int(value):
            with pytest.raises(ValueError):
                Quantity(value)

    @pytest.mark.property
    @given(st.integers(min_value=0, max_value=1000))
    def test_quantity_preserves_value(self, value):
        """Property: constructed Quantity should preserve the integer value."""
        q = Quantity(Decimal(str(value)))
        assert int(q.value) == value

    @pytest.mark.property
    @given(st.integers(min_value=0, max_value=1000), st.integers(min_value=0, max_value=1000))
    def test_quantity_comparison(self, value1, value2):
        """Property: Quantity comparison should match integer comparison."""
        q1 = Quantity(Decimal(str(value1)))
        q2 = Quantity(Decimal(str(value2)))

        if value1 < value2:
            assert q1.value < q2.value
        elif value1 > value2:
            assert q1.value > q2.value
        else:
            assert q1.value == q2.value
