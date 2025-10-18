"""Business Unit: shared | Status: current.

Comprehensive unit and property-based tests for numeric helper utilities.

This module tests float comparison logic with tolerance handling according
to project guardrails (no direct float ==).
"""

from decimal import Decimal

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.math.num import _extract_numeric_value, floats_equal


class TestExtractNumericValue:
    """Test numeric value extraction from various input types."""

    @pytest.mark.unit
    def test_extract_from_single_float(self):
        """Test extracting value from a single float."""
        assert _extract_numeric_value(3.14) == 3.14

    @pytest.mark.unit
    def test_extract_from_single_int(self):
        """Test extracting value from a single integer."""
        assert _extract_numeric_value(42) == 42

    @pytest.mark.unit
    def test_extract_from_decimal(self):
        """Test extracting value from a Decimal."""
        d = Decimal("123.456")
        assert _extract_numeric_value(d) == d

    @pytest.mark.unit
    def test_extract_from_list_with_single_element(self):
        """Test extracting value from a list with one element."""
        assert _extract_numeric_value([99.9]) == 99.9

    @pytest.mark.unit
    def test_extract_from_list_with_multiple_elements(self):
        """Test extracting first value from a list with multiple elements."""
        assert _extract_numeric_value([1.0, 2.0, 3.0]) == 1.0

    @pytest.mark.unit
    def test_extract_from_tuple(self):
        """Test extracting value from a tuple."""
        assert _extract_numeric_value((5.5, 6.6)) == 5.5

    @pytest.mark.unit
    def test_extract_from_empty_sequence_raises_value_error(self):
        """Test that empty sequences raise ValueError."""
        with pytest.raises(ValueError, match="Cannot compare empty sequence"):
            _extract_numeric_value([])

    @pytest.mark.unit
    def test_extract_from_empty_tuple_raises_value_error(self):
        """Test that empty tuples raise ValueError."""
        with pytest.raises(ValueError, match="Cannot compare empty sequence"):
            _extract_numeric_value(())

    @pytest.mark.unit
    def test_extract_from_string_raises_type_error(self):
        """Test that strings raise TypeError."""
        with pytest.raises(TypeError, match="Unsupported type"):
            _extract_numeric_value("not a number")

    @pytest.mark.unit
    def test_extract_from_none_raises_type_error(self):
        """Test that None raises TypeError."""
        with pytest.raises(TypeError, match="Unsupported type"):
            _extract_numeric_value(None)


class TestFloatsEqual:
    """Test float equality comparison with tolerance."""

    @pytest.mark.unit
    def test_equal_floats_returns_true(self):
        """Test that equal floats return True."""
        assert floats_equal(1.0, 1.0)

    @pytest.mark.unit
    def test_equal_integers_returns_true(self):
        """Test that equal integers return True."""
        assert floats_equal(5, 5)

    @pytest.mark.unit
    def test_close_floats_within_default_tolerance_returns_true(self):
        """Test that floats within default tolerance are equal."""
        assert floats_equal(1.0, 1.0 + 1e-10)
        assert floats_equal(1.0, 1.0 - 1e-10)

    @pytest.mark.unit
    def test_floats_outside_default_tolerance_returns_false(self):
        """Test that floats outside default tolerance are not equal."""
        assert not floats_equal(1.0, 1.0 + 1e-8)
        assert not floats_equal(1.0, 1.0 - 1e-8)

    @pytest.mark.unit
    def test_custom_relative_tolerance(self):
        """Test using custom relative tolerance."""
        # With default rel_tol=1e-9, these would be different
        # With rel_tol=1e-6, they should be equal
        assert floats_equal(1000.0, 1000.001, rel_tol=1e-6)

    @pytest.mark.unit
    def test_custom_absolute_tolerance(self):
        """Test using custom absolute tolerance."""
        # With default abs_tol=1e-12, these would be different
        # With abs_tol=0.01, they should be equal
        assert floats_equal(0.0, 0.005, abs_tol=0.01)
        assert not floats_equal(0.0, 0.02, abs_tol=0.01)

    @pytest.mark.unit
    def test_zero_comparison(self):
        """Test comparison with zero."""
        assert floats_equal(0.0, 0.0)
        assert floats_equal(0.0, 1e-13)
        assert not floats_equal(0.0, 1e-10)

    @pytest.mark.unit
    def test_negative_values(self):
        """Test comparison of negative values."""
        assert floats_equal(-1.0, -1.0)
        assert floats_equal(-5.5, -5.5 + 1e-10)
        assert not floats_equal(-1.0, -1.001)

    @pytest.mark.unit
    def test_mixed_signs_returns_false(self):
        """Test that mixed sign values are not equal."""
        assert not floats_equal(1.0, -1.0)
        assert not floats_equal(-0.5, 0.5)

    @pytest.mark.unit
    def test_decimal_comparison(self):
        """Test comparison of Decimal values."""
        assert floats_equal(Decimal("1.0"), Decimal("1.0"))
        assert floats_equal(Decimal("3.14159"), Decimal("3.14159"))
        assert not floats_equal(Decimal("1.0"), Decimal("1.01"))

    @pytest.mark.unit
    def test_mixed_int_and_float(self):
        """Test comparison of integers and floats."""
        assert floats_equal(5, 5.0)
        assert floats_equal(10.0, 10)
        assert not floats_equal(5, 5.1)

    @pytest.mark.unit
    def test_list_extraction_in_comparison(self):
        """Test that lists are extracted and compared."""
        assert floats_equal([1.0], [1.0])
        assert floats_equal([2.5], 2.5)
        assert floats_equal(3.0, [3.0])

    @pytest.mark.unit
    def test_numpy_array_comparison(self):
        """Test comparison of numpy arrays."""
        # Single element arrays
        assert floats_equal(np.array([1.0]), np.array([1.0]))

        # Arrays with same values
        assert floats_equal(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0]))

        # Arrays with different values
        assert not floats_equal(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.1]))

    @pytest.mark.unit
    def test_numpy_array_with_tolerance(self):
        """Test numpy array comparison with tolerance."""
        arr1 = np.array([1.0, 2.0, 3.0])
        arr2 = np.array([1.0 + 1e-10, 2.0 + 1e-10, 3.0 + 1e-10])
        assert floats_equal(arr1, arr2)

    @pytest.mark.unit
    def test_large_numbers(self):
        """Test comparison of large numbers."""
        large = 1e10
        assert floats_equal(large, large)
        assert floats_equal(large, large + 1.0, rel_tol=1e-9)
        assert not floats_equal(large, large + 1000.0, rel_tol=1e-9)

    @pytest.mark.unit
    def test_small_numbers_near_zero(self):
        """Test comparison of very small numbers near zero."""
        small = 1e-15
        assert floats_equal(small, small)
        assert floats_equal(small, 0.0, abs_tol=1e-14)
        assert not floats_equal(small, 1e-10)

    # Property-based tests using Hypothesis
    @pytest.mark.property
    @given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
    def test_reflexivity(self, x):
        """Property: any number should equal itself."""
        assert floats_equal(x, x)

    @pytest.mark.property
    @given(
        st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
        st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
    )
    def test_symmetry(self, x, y):
        """Property: if x equals y, then y equals x."""
        assert floats_equal(x, y) == floats_equal(y, x)

    @pytest.mark.property
    @given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
    def test_tiny_perturbation_within_default_tolerance(self, x):
        """Property: adding a tiny value should stay within tolerance."""
        if abs(x) > 1e-6:  # Avoid issues with very small numbers
            perturbation = x * 1e-10
            assert floats_equal(x, x + perturbation)

    @pytest.mark.property
    @given(
        st.decimals(
            min_value="-1000000",
            max_value="1000000",
            allow_nan=False,
            allow_infinity=False,
            places=6,
        )
    )
    def test_decimal_reflexivity(self, d):
        """Property: any Decimal should equal itself."""
        assert floats_equal(d, d)

    @pytest.mark.property
    @given(st.integers(min_value=-1000000, max_value=1000000))
    def test_integer_reflexivity(self, n):
        """Property: any integer should equal itself."""
        assert floats_equal(n, n)

    @pytest.mark.property
    @given(
        st.floats(min_value=0.1, max_value=1e6, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1e-6, max_value=1e-3),
    )
    def test_relative_tolerance_bounds(self, base, rel_tol):
        """Property: values within relative tolerance are equal."""
        offset = base * (rel_tol / 2)  # Half the tolerance
        assert floats_equal(base, base + offset, rel_tol=rel_tol)
        assert floats_equal(base, base - offset, rel_tol=rel_tol)

    @pytest.mark.property
    @given(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1e-6, max_value=1e-3),
    )
    def test_absolute_tolerance_bounds(self, base, abs_tol):
        """Property: values within absolute tolerance are equal."""
        offset = abs_tol / 2  # Half the tolerance
        assert floats_equal(base, base + offset, abs_tol=abs_tol)
        assert floats_equal(base, base - offset, abs_tol=abs_tol)

    @pytest.mark.property
    @given(
        st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10,
        )
    )
    def test_numpy_array_reflexivity(self, values):
        """Property: any numpy array should equal itself."""
        arr = np.array(values)
        assert floats_equal(arr, arr)
