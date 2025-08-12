import pytest
from hypothesis import given, strategies as st

from the_alchemiser.utils.num import floats_equal


@given(st.floats(allow_nan=False, allow_infinity=False, width=64))
def test_floats_equal_reflexive(x):
    """floats_equal should treat a value as equal to itself."""
    assert floats_equal(x, x)


@pytest.mark.parametrize(
    "a, b",
    [
        (0.1 + 0.2, 0.3),  # classic floating point rounding
        (1.000000001, 1.000000002),  # within tolerance
    ],
)
def test_floats_equal_known_cases(a, b):
    """floats_equal should consider nearly identical floats equal."""
    assert floats_equal(a, b)
