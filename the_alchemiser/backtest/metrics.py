"""Basic performance metrics."""

from collections.abc import Iterable

from ..execution.models import Fill


def equity_curve(fills: Iterable[Fill]) -> list[float]:  # pragma: no cover - stub
    """Return cumulative P&L curve."""
    total = 0.0
    curve = []
    for f in fills:
        total += f.qty * f.price
        curve.append(total)
    return curve
