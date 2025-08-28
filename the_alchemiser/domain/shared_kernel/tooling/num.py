"""Business Unit: utilities; Status: current.

Numeric helper utilities for cross-context use.

Provides tolerant float comparison complying with project rule: never use
direct float equality (== / !=). Use this helper in non-financial contexts;
for money/quantities always prefer Decimal value objects.

NOTE: This module must remain framework-agnostic and side-effect free
to comply with shared kernel principles.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from math import isclose

try:
    import numpy as np
except ImportError:  # pragma: no cover - numpy optional
    np = None  # type: ignore[assignment]


Number = float | int | Decimal
SequenceLike = Sequence[Number] | Number


def floats_equal(
    a: SequenceLike, b: SequenceLike, rel_tol: float = 1e-9, abs_tol: float = 1e-12
) -> bool:
    """Check whether two floating-point values are approximately equal.

    This function provides safe float comparison that complies with the project
    policy of never using direct float equality (== / !=). Use this for
    non-financial numeric comparisons; for money/quantities use Decimal objects.

    Args:
        a: First value or array to compare.
        b: Second value or array to compare.
        rel_tol: Relative tolerance for comparison.
        abs_tol: Absolute tolerance for comparison.

    Returns:
        bool: True if the values are equal within the given tolerances; otherwise False.

    Raises:
        ValueError: If comparing empty sequences.
        TypeError: If unsupported types are provided.

    Example:
        >>> floats_equal(0.1 + 0.2, 0.3)
        True
        >>> floats_equal(1.0, 1.000001, rel_tol=1e-5)
        True
    """
    try:
        if np is not None and (isinstance(a, np.ndarray) or isinstance(b, np.ndarray)):
            return bool(np.isclose(a, b, rtol=rel_tol, atol=abs_tol, equal_nan=False).all())
    except (
        TypeError,
        ValueError,
        AttributeError,
    ):  # pragma: no cover - fall back to scalar comparison
        pass

    # Handle sequence types by comparing first elements or raise error for invalid sequences
    a_val: Number
    b_val: Number

    if isinstance(a, Sequence) and not isinstance(a, str | bytes):
        if len(a) == 0:
            raise ValueError("Cannot compare empty sequence")
        a_val = a[0]
    elif isinstance(a, Number):
        a_val = a
    else:
        raise TypeError(f"Unsupported type for comparison: {type(a)}")

    if isinstance(b, Sequence) and not isinstance(b, str | bytes):
        if len(b) == 0:
            raise ValueError("Cannot compare empty sequence")
        b_val = b[0]
    elif isinstance(b, Number):
        b_val = b
    else:
        raise TypeError(f"Unsupported type for comparison: {type(b)}")

    return isclose(float(a_val), float(b_val), rel_tol=rel_tol, abs_tol=abs_tol)