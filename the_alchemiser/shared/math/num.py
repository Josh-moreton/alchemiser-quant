"""Business Unit: utilities; Status: current.

Numeric helper utilities.

Provides tolerant float comparison complying with project rule: never use
direct float equality (== / !=). Use this helper in non-financial contexts;
for money/quantities always prefer Decimal value objects.
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


def _extract_numeric_value(value: SequenceLike) -> Number:
    """Extract a numeric value from a sequence or number.
    
    Args:
        value: Input value (number or sequence)
        
    Returns:
        Extracted numeric value
        
    Raises:
        ValueError: For empty sequences
        TypeError: For unsupported types

    """
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        if len(value) == 0:
            raise ValueError("Cannot compare empty sequence")
        return value[0]
    if isinstance(value, Number):
        return value
    raise TypeError(f"Unsupported type for comparison: {type(value)}")


def floats_equal(
    a: SequenceLike, b: SequenceLike, rel_tol: float = 1e-9, abs_tol: float = 1e-12
) -> bool:
    """Check whether two floating-point values are approximately equal.

    Args:
        a: First value or array to compare.
        b: Second value or array to compare.
        rel_tol: Relative tolerance for comparison.
        abs_tol: Absolute tolerance for comparison.

    Returns:
        bool: True if the values are equal within the given tolerances; otherwise False.

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

    # Handle sequence types by extracting numeric values
    a_val = _extract_numeric_value(a)
    b_val = _extract_numeric_value(b)

    return isclose(float(a_val), float(b_val), rel_tol=rel_tol, abs_tol=abs_tol)
