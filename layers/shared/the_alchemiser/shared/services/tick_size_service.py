"""Business Unit: shared | Status: current.

Simple tick size service for trading calculations.

Provides symbol-specific tick sizes for order pricing calculations.
"""

from __future__ import annotations

from decimal import Decimal


class TickSizeService:
    """Simple tick size service for trading calculations."""

    def get_tick_size(self, _symbol: str, price: Decimal) -> Decimal:
        """Get tick size for a symbol at a given price.

        Args:
            _symbol: Trading symbol (currently unused, using simple price-based rules)
            price: Current price

        Returns:
            Tick size as Decimal

        """
        # Simple implementation - most stocks use penny increments
        # In a full implementation, this would consider:
        # - Symbol-specific rules
        # - Price-based rules (e.g., stocks over $1 vs under $1)
        # - Market-specific rules

        if price < Decimal("1.00"):
            # Sub-dollar stocks often use smaller increments
            return Decimal("0.0001")
        # Most stocks use penny increments
        return Decimal("0.01")


# Alias for backward compatibility
DynamicTickSizeService = TickSizeService
