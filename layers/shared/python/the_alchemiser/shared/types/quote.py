"""Business Unit: shared | Status: current.

Legacy domain model for a simplified bid/ask quote.

NOTE: A more complete QuoteModel exists in the_alchemiser.shared.types.market_data
with additional fields (bid_size, ask_size, symbol). Consider using that model
for new code requiring market depth information.

This model is maintained for backward compatibility with existing code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class QuoteModel:
    """Market quote with bid/ask prices and timestamp.

    Represents a point-in-time bid/ask quote for a financial instrument.

    Attributes:
        ts: Quote timestamp (UTC), or None if timestamp unavailable
        bid: Bid price as Decimal (precision typically 2-4 decimal places)
        ask: Ask price as Decimal (precision typically 2-4 decimal places)

    Properties:
        mid: Calculated mid-point price (bid + ask) / 2

    Invariants:
        - bid and ask should be positive (not enforced; validation at boundaries)
        - bid should typically be <= ask (not enforced; validation at boundaries)

    Examples:
        >>> from datetime import datetime, UTC
        >>> from decimal import Decimal
        >>> quote = QuoteModel(ts=datetime.now(UTC), bid=Decimal("100.00"), ask=Decimal("100.25"))
        >>> quote.mid
        Decimal('100.125')

    Note:
        For market depth information (bid_size, ask_size), consider using
        QuoteModel from the_alchemiser.shared.types.market_data instead.

    """

    ts: datetime | None
    bid: Decimal
    ask: Decimal

    @property
    def mid(self) -> Decimal:
        """Calculate the mid-point price between bid and ask.

        Returns:
            Decimal: The mid-point price, calculated as (bid + ask) / 2

        """
        return (self.bid + self.ask) / Decimal("2")
