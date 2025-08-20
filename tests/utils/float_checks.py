from collections.abc import Iterable
from math import isclose

import numpy as np
import pytest


def approx_eq(a: float, b: float, *, rtol: float = 1e-6, atol: float = 0.0) -> bool:
    return isclose(a, b, rel_tol=rtol, abs_tol=atol)


def assert_close(a: float, b: float, *, rtol: float = 1e-6, atol: float = 0.0) -> None:
    assert a == pytest.approx(b, rel=rtol, abs=atol)


def assert_array_close(
    a: Iterable[float], b: Iterable[float], *, rtol: float = 1e-6, atol: float = 0.0
) -> None:
    np.testing.assert_allclose(a, b, rtol=rtol, atol=atol)
