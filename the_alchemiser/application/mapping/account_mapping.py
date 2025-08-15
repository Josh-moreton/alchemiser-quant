from __future__ import annotations

from decimal import Decimal

from the_alchemiser.domain.shared_kernel.value_objects.money import Money


def to_money_usd(value: str | float | int | Decimal | None) -> Money | None:
    """Map raw numeric portfolio value to Money(USD).

    Returns None if value is None or not coercible.
    """
    if value is None:
        return None
    try:
        dec = Decimal(str(value))
    except Exception:
        return None
    return Money(dec, "USD")
