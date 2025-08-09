from math import isclose
from typing import Any

try:
    import numpy as np
except ImportError:  # pragma: no cover - numpy optional
    np = None  # type: ignore[assignment]


def floats_equal(a: Any, b: Any, rel_tol: float = 1e-9, abs_tol: float = 1e-12) -> bool:
    """Compare two floats or arrays with tolerance."""
    try:
        if np is not None and (isinstance(a, np.ndarray) or isinstance(b, np.ndarray)):
            return bool(np.isclose(a, b, rtol=rel_tol, atol=abs_tol, equal_nan=False).all())
    except (TypeError, ValueError, AttributeError):  # pragma: no cover - fall back to scalar comparison
        pass
    return isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=abs_tol)
