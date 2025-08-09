import math

import numpy as np

from the_alchemiser.utils.num import floats_equal


def test_floats_equal_basic():
    assert floats_equal(0.1 + 0.2, 0.3)
    assert floats_equal(0.1, 0.10000000005)
    assert not floats_equal(0.1, 0.1001)


def test_floats_equal_nan():
    assert not floats_equal(math.nan, math.nan)


def test_floats_equal_numpy():
    arr1 = np.array([0.1, 0.2])
    arr2 = np.array([0.1, 0.2 + 1e-10])
    assert floats_equal(arr1, arr2)
    arr3 = np.array([0.1, 0.2 + 1e-6])
    assert not floats_equal(arr1, arr3)
