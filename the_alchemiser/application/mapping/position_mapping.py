from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class PositionSummary:
    symbol: str
    qty: Decimal
    avg_entry_price: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pl: Decimal
    unrealized_plpc: Decimal


def _to_decimal(val: object) -> Decimal:
    try:
        if val is None:
            return Decimal("0")
        return Decimal(str(val))
    except Exception:
        return Decimal("0")


def alpaca_position_to_summary(pos: object) -> PositionSummary:
    """Map an Alpaca Position (object or dict) to a normalized PositionSummary."""
    if isinstance(pos, dict):
        symbol = str(pos.get("symbol", ""))
        qty = _to_decimal(pos.get("qty", 0))
        avg_entry_price = _to_decimal(pos.get("avg_entry_price", 0))
        current_price = _to_decimal(pos.get("current_price", 0))
        market_value = _to_decimal(pos.get("market_value", 0))
        unrealized_pl = _to_decimal(pos.get("unrealized_pl", 0))
        unrealized_plpc = _to_decimal(pos.get("unrealized_plpc", 0))
    else:
        symbol = str(getattr(pos, "symbol", ""))
        qty = _to_decimal(getattr(pos, "qty", 0))
        avg_entry_price = _to_decimal(getattr(pos, "avg_entry_price", 0))
        current_price = _to_decimal(getattr(pos, "current_price", 0))
        market_value = _to_decimal(getattr(pos, "market_value", 0))
        unrealized_pl = _to_decimal(getattr(pos, "unrealized_pl", 0))
        unrealized_plpc = _to_decimal(getattr(pos, "unrealized_plpc", 0))

    return PositionSummary(
        symbol=symbol,
        qty=qty,
        avg_entry_price=avg_entry_price,
        current_price=current_price,
        market_value=market_value,
        unrealized_pl=unrealized_pl,
        unrealized_plpc=unrealized_plpc,
    )
