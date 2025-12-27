"""Business Unit: shared; Status: current.

Asset Metadata Provider Protocol.

Protocol Version: 1.0.0

Defines the interface for accessing asset metadata like fractionability,
asset types, and trading characteristics. This protocol keeps the domain
layer pure by avoiding direct infrastructure dependencies.

Usage:
    Implementations of this protocol provide asset metadata access without
    coupling domain logic to specific broker APIs. The protocol defines the
    contract for querying asset characteristics needed for trading decisions.

    Example implementation:
        class AlpacaAssetMetadataAdapter(AssetMetadataProvider):
            def is_fractionable(self, symbol: Symbol) -> bool:
                return self._alpaca_manager.is_fractionable(str(symbol))

    Example usage:
        provider: AssetMetadataProvider = get_asset_metadata_provider()
        if provider.is_fractionable(Symbol("AAPL")):
            # Can trade fractional shares
            ...
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Literal, Protocol

from the_alchemiser.shared.value_objects.symbol import Symbol

__version__ = "1.0.0"

# Type alias for asset class return values
AssetClass = Literal["us_equity", "crypto", "unknown"]


class AssetMetadataProvider(Protocol):
    """Protocol for accessing asset metadata and trading characteristics.

    This protocol defines the interface for querying asset metadata required
    for trading decisions, such as fractionability support, asset classification,
    and order type determination.
    """

    @abstractmethod
    def is_fractionable(self, symbol: Symbol) -> bool:
        """Check if an asset supports fractional shares.

        Args:
            symbol: The symbol to check

        Returns:
            True if the asset supports fractional shares, False otherwise

        Raises:
            RateLimitError: If broker API rate limit exceeded (should be retried)
            DataProviderError: If asset not found or data unavailable

        """
        ...

    @abstractmethod
    def get_asset_class(self, symbol: Symbol) -> AssetClass:
        """Get the asset class for a symbol.

        Args:
            symbol: The symbol to classify

        Returns:
            Asset class: 'us_equity' for stocks/ETFs, 'crypto' for cryptocurrencies,
            'unknown' if classification unavailable

        Raises:
            RateLimitError: If broker API rate limit exceeded (should be retried)
            DataProviderError: If asset not found or data unavailable

        """
        ...

    @abstractmethod
    def should_use_notional_order(self, symbol: Symbol, quantity: float) -> bool:
        """Determine if notional (dollar) orders should be used.

        Notional orders specify trade value in dollars rather than share quantity.
        They are typically used for non-fractionable assets, very small quantities
        (< 1 share), or when fractional parts are significant (> 0.1).

        Args:
            symbol: The symbol to trade
            quantity: Intended quantity (must be > 0)

        Returns:
            True if notional orders should be used, False for quantity-based orders

        Raises:
            ValueError: If quantity <= 0
            RateLimitError: If broker API rate limit exceeded (should be retried)
            DataProviderError: If asset not found or data unavailable

        """
        ...
