"""Business Unit: shared/math; Status: current.

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
    from the_alchemiser.shared.logging import get_logger
    logger = get_logger(__name__)
except ImportError:  # pragma: no cover - logging optional
    import logging
    logger = logging.getLogger(__name__)

try:
    import numpy as np
except ImportError:  # pragma: no cover - numpy optional (gracefully degrades to scalar comparison)
    np = None  # type: ignore[assignment]


Number = float | int | Decimal
SequenceLike = Sequence[Number] | Number

__all__ = ["floats_equal", "Number", "SequenceLike"]


def _extract_numeric_value(value: SequenceLike) -> Number:
    """Extract a numeric value from a sequence or number.

    Returns first element of sequence. Assumes sequences contain homogeneous
    numeric values; only the first element is used for comparison.

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

    Uses relative and absolute tolerances to determine equality. This function
    should be used for non-financial float comparisons. For money/quantities,
    always use Decimal value objects.

    Default tolerances chosen to balance precision and practicality:
    - rel_tol=1e-9: ~9 decimal places relative precision
    - abs_tol=1e-12: ~12 decimal places absolute precision near zero
    These match Python's math.isclose defaults for consistency.

    Args:
        a: First value or array to compare.
        b: Second value or array to compare.
        rel_tol: Relative tolerance for comparison (default: 1e-9).
        abs_tol: Absolute tolerance for comparison (default: 1e-12).

    Returns:
        bool: True if the values are equal within the given tolerances.

    Examples:
        >>> floats_equal(1.0, 1.0)
        True
        >>> floats_equal(1.0, 1.0 + 1e-10)  # Within default tolerance
        True
        >>> floats_equal(1.0, 1.001)  # Outside default tolerance
        False
        >>> floats_equal(0.0, 1e-13)  # Near-zero comparison uses abs_tol
        True

    Note:
        - NaN values are never equal to each other or any other value
        - Infinity comparisons use standard float comparison rules
        - For numpy arrays, all elements must be within tolerance
        - Sequence inputs use first element only
        - When comparing Decimal values, they are converted to float which may
          lose precision. This is acceptable for non-financial comparisons but
          means extremely precise Decimal values (>15 significant figures) may
          not compare accurately. For financial values, use Decimal directly.

    """
    try:
        if np is not None and (isinstance(a, np.ndarray) or isinstance(b, np.ndarray)):
            return bool(np.isclose(a, b, rtol=rel_tol, atol=abs_tol, equal_nan=False).all())
    except (
        TypeError,
        ValueError,
        AttributeError,
    ) as e:  # pragma: no cover - fall back to scalar comparison
        logger.debug(f"Numpy comparison failed, falling back to scalar: {e}")

    # Handle sequence types by extracting numeric values
    a_val = _extract_numeric_value(a)
    b_val = _extract_numeric_value(b)

    return isclose(float(a_val), float(b_val), rel_tol=rel_tol, abs_tol=abs_tol)
