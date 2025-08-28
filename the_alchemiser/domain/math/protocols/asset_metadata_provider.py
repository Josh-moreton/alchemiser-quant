"""Business Unit: utilities; Status: current.

Asset metadata provider protocol for domain dependency injection.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.domain.shared_kernel.value_objects.symbol import Symbol


class AssetMetadataProvider(Protocol):
    """Protocol for providing asset metadata without infrastructure dependencies."""

    def is_fractionable(self, symbol: Symbol) -> bool:
        """Check if an asset supports fractional shares.

        Args:
            symbol: Symbol to check

        Returns:
            True if asset supports fractional shares

        """
        ...

    def should_use_notional_order(self, symbol: Symbol, quantity: float) -> bool:
        """Determine if notional (dollar) orders should be used.

        Args:
            symbol: Symbol to check
            quantity: Intended quantity to trade

        Returns:
            True if should use notional order

        """
        ...

    def convert_to_whole_shares(
        self, symbol: Symbol, quantity: float, current_price: float
    ) -> tuple[float, bool]:
        """Convert fractional quantity to whole shares if needed.

        Args:
            symbol: Symbol to check
            quantity: Fractional quantity desired
            current_price: Current price per share

        Returns:
            Tuple of (adjusted_quantity, used_rounding)

        """
        ...