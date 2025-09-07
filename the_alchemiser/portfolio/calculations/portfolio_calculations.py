"""Business Unit: portfolio assessment & management; Status: current.

Portfolio calculation utilities (business logic only).

Moved from interface layer to application.trading to maintain layering:
application may not import interface/cli. Provides pure allocation calculations.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
from typing_extensions import TypedDict

from the_alchemiser.shared.value_objects.core_types import AccountInfo, PositionInfo, PositionsDict

# NOTE: We handle position value extraction inline to avoid external dependencies
# for simple calculations. All values are promoted to Decimal for precision.


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _extract_current_position_values(current_positions: dict[str, Any]) -> dict[str, float]:
    """Extract current market values from position objects.

    Args:
        current_positions: Dictionary mapping symbols to position objects

    Returns:
        Dictionary mapping symbols to current market values

    """
    current_values: dict[str, float] = {}
    for symbol, pos in current_positions.items():
        try:
            current_values[symbol] = float(pos["market_value"])
        except (ValueError, TypeError, KeyError):
            current_values[symbol] = 0.0
    return current_values


def calculate_target_vs_current_allocations(
    target_portfolio: dict[str, float],
    account_info: AccountInfo | dict[str, Any],
    current_positions: PositionsDict | dict[str, PositionInfo | dict[str, Any] | Any],
) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """Calculate target vs current allocations using Decimal values.

    Args:
        target_portfolio: mapping symbol -> target weight (0-1 float)
        account_info: account info (TypedDict or legacy dict)
        current_positions: mapping symbol -> position info

    Returns:
        (target_values, current_values) both symbol -> Decimal dollar value

    """
    # Normalize account info to AccountInfo TypedDict compatible dict
    # AccountInfo is a TypedDict (dict subclass) so isinstance(account_info, dict) is always True.
    # Keep a single branch to avoid mypy unreachable code warning.
    portfolio_value = _to_decimal(
        (account_info.get("portfolio_value") if isinstance(account_info, dict) else None)
        or (account_info.get("equity") if isinstance(account_info, dict) else None)
        or 0
    )

    # Recompute target values with Decimal precision
    target_values: dict[str, Decimal] = {}
    for symbol, weight in target_portfolio.items():
        try:
            w = Decimal(str(weight))
        except (InvalidOperation, ValueError):
            w = Decimal("0")
        target_values[symbol] = (portfolio_value * w).quantize(Decimal("0.01"))

    # Current values: leverage existing helper then convert
    # Narrow type for helper expecting PositionsDict; fall back to empty mapping if incompatible shapes
    if all(isinstance(v, dict) and "market_value" in v for v in current_positions.values()):
        float_current = _extract_current_position_values(current_positions)
    else:  # pragma: no cover - defensive fallback
        float_current = {}
    current_values: dict[str, Decimal] = {
        sym: _to_decimal(val).quantize(Decimal("0.01")) for sym, val in float_current.items()
    }

    return target_values, current_values


class AllocationComparison(TypedDict):
    """Structured comparison for allocations with Decimal precision."""

    target_values: dict[str, Decimal]
    current_values: dict[str, Decimal]
    deltas: dict[str, Decimal]


def build_allocation_comparison(
    target_portfolio: dict[str, float],
    account_info: AccountInfo | dict[str, Any],
    current_positions: PositionsDict | dict[str, PositionInfo | dict[str, Any] | Any],
) -> AllocationComparison:
    """Return structured allocation comparison including deltas (target - current).

    Returns:
        AllocationComparison: target/current values and deltas by symbol (quantized 0.01)

    """
    target_values, current_values = calculate_target_vs_current_allocations(
        target_portfolio, account_info, current_positions
    )
    symbols = set(target_values.keys()) | set(current_values.keys())
    deltas: dict[str, Decimal] = {}
    for sym in symbols:
        t = target_values.get(sym, Decimal("0"))
        c = current_values.get(sym, Decimal("0"))
        deltas[sym] = (t - c).quantize(Decimal("0.01"))
    return AllocationComparison(
        target_values=target_values, current_values=current_values, deltas=deltas
    )


__all__ = [
    "AllocationComparison",
    "build_allocation_comparison",
    "calculate_target_vs_current_allocations",
]
