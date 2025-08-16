import numpy as np
from hypothesis import given, strategies as st

from the_alchemiser.utils.num import floats_equal


@given(st.floats(allow_nan=False), st.floats(allow_nan=False))
def test_floats_equal_symmetric(a, b):
    assert floats_equal(a, b) == floats_equal(b, a)


@given(st.lists(st.floats(allow_nan=False), min_size=1, max_size=5))
def test_floats_equal_numpy_arrays(xs):
    arr1 = np.array(xs)
    arr2 = np.array(xs)
    assert floats_equal(arr1, arr2)
