"""Business Unit: shared | Status: current.

Comprehensive unit and property-based tests for Percentage value object.

Tests Percentage value object operations with Decimal arithmetic and
validation per project guardrails.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.types.percentage import Percentage


class TestPercentageConstruction:
    """Test Percentage value object construction and validation."""

    @pytest.mark.unit
    def test_create_valid_percentage_zero(self):
        """Test creating Percentage with value 0 (0%)."""
        p = Percentage(Decimal("0"))
        assert p.value == Decimal("0")

    @pytest.mark.unit
    def test_create_valid_percentage_one(self):
        """Test creating Percentage with value 1 (100%)."""
        p = Percentage(Decimal("1"))
        assert p.value == Decimal("1")

    @pytest.mark.unit
    def test_create_valid_percentage_half(self):
        """Test creating Percentage with value 0.5 (50%)."""
        p = Percentage(Decimal("0.5"))
        assert p.value == Decimal("0.5")

    @pytest.mark.unit
    def test_create_valid_percentage_quarter(self):
        """Test creating Percentage with value 0.25 (25%)."""
        p = Percentage(Decimal("0.25"))
        assert p.value == Decimal("0.25")

    @pytest.mark.unit
    def test_negative_percentage_raises_value_error(self):
        """Test that negative percentages raise ValueError."""
        with pytest.raises(ValueError, match="must be between"):
            Percentage(Decimal("-0.1"))

    @pytest.mark.unit
    def test_percentage_above_one_raises_value_error(self):
        """Test that percentages > 1.0 raise ValueError."""
        with pytest.raises(ValueError, match="must be between"):
            Percentage(Decimal("1.1"))

    @pytest.mark.unit
    def test_percentage_far_above_one_raises_value_error(self):
        """Test that percentages significantly > 1.0 raise ValueError."""
        with pytest.raises(ValueError, match="must be between"):
            Percentage(Decimal("100"))

    @pytest.mark.unit
    def test_percentage_is_frozen(self):
        """Test that Percentage is immutable (frozen dataclass)."""
        p = Percentage(Decimal("0.5"))
        with pytest.raises(AttributeError):
            p.value = Decimal("0.7")


class TestPercentageFromPercent:
    """Test Percentage.from_percent class method."""

    @pytest.mark.unit
    def test_from_percent_zero(self):
        """Test creating Percentage from 0 percent."""
        p = Percentage.from_percent(0.0)
        assert p.value == Decimal("0")

    @pytest.mark.unit
    def test_from_percent_hundred(self):
        """Test creating Percentage from 100 percent."""
        p = Percentage.from_percent(100.0)
        assert p.value == Decimal("1")

    @pytest.mark.unit
    def test_from_percent_fifty(self):
        """Test creating Percentage from 50 percent."""
        p = Percentage.from_percent(50.0)
        assert p.value == Decimal("0.5")

    @pytest.mark.unit
    def test_from_percent_twenty_five(self):
        """Test creating Percentage from 25 percent."""
        p = Percentage.from_percent(25.0)
        assert p.value == Decimal("0.25")

    @pytest.mark.unit
    def test_from_percent_decimal_value(self):
        """Test creating Percentage from decimal percent value."""
        p = Percentage.from_percent(33.33)
        assert p.value == Decimal("0.3333")

    @pytest.mark.unit
    def test_from_percent_negative_raises_value_error(self):
        """Test that negative percent values raise ValueError."""
        with pytest.raises(ValueError, match="must be between"):
            Percentage.from_percent(-10.0)

    @pytest.mark.unit
    def test_from_percent_above_hundred_raises_value_error(self):
        """Test that percent values > 100 raise ValueError."""
        with pytest.raises(ValueError, match="must be between"):
            Percentage.from_percent(150.0)


class TestPercentageToPercent:
    """Test Percentage.to_percent method."""

    @pytest.mark.unit
    def test_to_percent_zero(self):
        """Test converting 0.0 to percent representation."""
        p = Percentage(Decimal("0"))
        assert p.to_percent() == Decimal("0")

    @pytest.mark.unit
    def test_to_percent_one(self):
        """Test converting 1.0 to percent representation."""
        p = Percentage(Decimal("1"))
        assert p.to_percent() == Decimal("100")

    @pytest.mark.unit
    def test_to_percent_half(self):
        """Test converting 0.5 to percent representation."""
        p = Percentage(Decimal("0.5"))
        assert p.to_percent() == Decimal("50")

    @pytest.mark.unit
    def test_to_percent_quarter(self):
        """Test converting 0.25 to percent representation."""
        p = Percentage(Decimal("0.25"))
        assert p.to_percent() == Decimal("25")

    @pytest.mark.unit
    def test_to_percent_decimal_value(self):
        """Test converting decimal value to percent."""
        p = Percentage(Decimal("0.3333"))
        assert p.to_percent() == Decimal("33.33")


class TestPercentageRoundTrip:
    """Test round-trip conversion between value and percent."""

    @pytest.mark.unit
    def test_roundtrip_from_percent_to_percent(self):
        """Test round-trip: percent -> Percentage -> percent."""
        original_percent = 75.0
        p = Percentage.from_percent(original_percent)
        result_percent = p.to_percent()

        assert result_percent == Decimal("75")

    @pytest.mark.unit
    def test_roundtrip_value_to_value(self):
        """Test round-trip: value -> to_percent -> from_percent -> value."""
        original_value = Decimal("0.6")
        p = Percentage(original_value)
        percent = p.to_percent()
        p2 = Percentage.from_percent(float(percent))

        assert p2.value == original_value


# Property-based tests using Hypothesis
class TestPercentageProperties:
    """Property-based tests for Percentage value object."""

    @pytest.mark.property
    @given(
        st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False, places=4)
    )
    def test_construction_preserves_range(self, value):
        """Property: constructed Percentage should always be in [0, 1]."""
        p = Percentage(value)
        assert Decimal("0") <= p.value <= Decimal("1")

    @pytest.mark.property
    @given(st.floats(min_value=0.0, max_value=100.0))
    def test_from_percent_preserves_range(self, percent):
        """Property: from_percent should create valid Percentage in [0, 1]."""
        p = Percentage.from_percent(percent)
        assert Decimal("0") <= p.value <= Decimal("1")

    @pytest.mark.property
    @given(
        st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False, places=4)
    )
    def test_to_percent_in_range(self, value):
        """Property: to_percent should return value in [0, 100]."""
        p = Percentage(value)
        percent = p.to_percent()
        assert Decimal("0") <= percent <= Decimal("100")

    @pytest.mark.property
    @given(st.floats(min_value=0.0, max_value=100.0))
    def test_roundtrip_from_percent(self, original_percent):
        """Property: round-trip from_percent -> to_percent should preserve value."""
        p = Percentage.from_percent(original_percent)
        result_percent = float(p.to_percent())

        # Allow small rounding error due to Decimal conversion
        assert abs(result_percent - original_percent) < 0.01

    @pytest.mark.property
    @given(
        st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False, places=2)
    )
    def test_roundtrip_value(self, original_value):
        """Property: round-trip value -> to_percent -> from_percent should preserve value."""
        p1 = Percentage(original_value)
        percent = p1.to_percent()
        p2 = Percentage.from_percent(float(percent))

        # Allow small rounding error
        assert abs(p2.value - original_value) <= Decimal("0.01")

    @pytest.mark.property
    @given(
        st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False, places=4)
    )
    def test_percent_conversion_linearity(self, value):
        """Property: to_percent should scale value by 100."""
        p = Percentage(value)
        percent = p.to_percent()

        expected = value * Decimal("100")
        assert percent == expected

    @pytest.mark.property
    @given(st.floats(min_value=0.01, max_value=99.99))
    def test_from_percent_conversion_linearity(self, percent):
        """Property: from_percent should divide by 100."""
        p = Percentage.from_percent(percent)

        expected = Decimal(str(percent)) / Decimal("100")
        # Allow small rounding error
        assert abs(p.value - expected) <= Decimal("0.0001")

    @pytest.mark.property
    @given(
        st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False, places=4),
        st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False, places=4),
    )
    def test_ordering_preserved(self, value1, value2):
        """Property: if value1 < value2, then percent1 < percent2."""
        if value1 == value2:
            return

        p1 = Percentage(value1)
        p2 = Percentage(value2)

        percent1 = p1.to_percent()
        percent2 = p2.to_percent()

        if value1 < value2:
            assert percent1 < percent2
        else:
            assert percent1 > percent2

    @pytest.mark.property
    @given(
        st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False, places=4)
    )
    def test_zero_comparison(self, value):
        """Property: percentage comparisons with zero should be consistent."""
        p = Percentage(value)

        if value == Decimal("0"):
            assert p.to_percent() == Decimal("0")
        else:
            assert p.to_percent() > Decimal("0")

    @pytest.mark.property
    @given(
        st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False, places=4)
    )
    def test_one_comparison(self, value):
        """Property: percentage comparisons with one (100%) should be consistent."""
        p = Percentage(value)

        if value == Decimal("1"):
            assert p.to_percent() == Decimal("100")
        else:
            assert p.to_percent() < Decimal("100")
