"""Tracking data normalization utilities.

Centralized quantization and normalization for strategy tracking data to ensure
consistent precision handling and avoid float comparison issues.

Design:
- Single responsibility: normalize tracking data at ingestion point
- Consistent decimal precision: price (4-6 dp), quantity (6 dp), money (2 dp)
- ROUND_HALF_UP rounding for financial consistency
- Reuse existing execution mapping helpers where appropriate
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

# Re-export precision helpers from execution mapping
from the_alchemiser.application.mapping.execution import ensure_money, ensure_quantity


def ensure_price(value: float | str | Decimal | int | None, decimal_places: int = 4) -> Decimal:
    """Quantize price values to specified decimal places using ROUND_HALF_UP.

    Args:
        value: Price value to quantize
        decimal_places: Number of decimal places (default 4, can be 6 for high-precision assets)

    Returns:
        Quantized Decimal price

    """
    if value is None:
        return Decimal("0")

    decimal_val = Decimal(str(value))
    quantizer = Decimal("0." + "0" * decimal_places)
    return decimal_val.quantize(quantizer, rounding=ROUND_HALF_UP)


def normalize_tracking_order(order_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize order data for tracking persistence.

    Ensures consistent precision for monetary values, quantities, and prices
    at the point of ingestion to avoid downstream precision issues.

    Args:
        order_data: Raw order data dictionary

    Returns:
        Normalized order data with quantized values

    """
    normalized = order_data.copy()

    # Normalize monetary fields (2 decimal places)
    if "filled_avg_price" in normalized:
        normalized["filled_avg_price"] = str(ensure_money(normalized["filled_avg_price"]))
    if "notional" in normalized:
        normalized["notional"] = str(ensure_money(normalized["notional"]))

    # Normalize quantity fields (6 decimal places for fractional shares)
    if "qty" in normalized:
        normalized["qty"] = str(ensure_quantity(normalized["qty"]))
    if "filled_qty" in normalized:
        normalized["filled_qty"] = str(ensure_quantity(normalized["filled_qty"]))

    # Normalize price fields (4 decimal places, can be adjusted for crypto/forex)
    if "limit_price" in normalized:
        normalized["limit_price"] = str(ensure_price(normalized["limit_price"]))
    if "stop_price" in normalized:
        normalized["stop_price"] = str(ensure_price(normalized["stop_price"]))

    return normalized


def normalize_pnl_summary(pnl_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize P&L summary data for consistent tracking.

    Args:
        pnl_data: Raw P&L data dictionary

    Returns:
        Normalized P&L data with quantized values

    """
    normalized = pnl_data.copy()

    # Normalize monetary P&L fields (2 decimal places)
    if "total_pnl" in normalized:
        normalized["total_pnl"] = str(ensure_money(normalized["total_pnl"]))
    if "realized_pnl" in normalized:
        normalized["realized_pnl"] = str(ensure_money(normalized["realized_pnl"]))
    if "unrealized_pnl" in normalized:
        normalized["unrealized_pnl"] = str(ensure_money(normalized["unrealized_pnl"]))
    if "cost_basis" in normalized:
        normalized["cost_basis"] = str(ensure_money(normalized["cost_basis"]))

    # Normalize percentage fields (4 decimal places for precision)
    if "return_pct" in normalized:
        normalized["return_pct"] = str(ensure_price(normalized["return_pct"]))

    return normalized
