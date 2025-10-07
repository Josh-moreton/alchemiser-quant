"""Business Unit: shared; Status: current.

Alpaca Asset Metadata Adapter.

Provides AssetMetadataProvider implementation using AlpacaManager,
bridging the domain protocol with the Alpaca broker infrastructure.

This adapter handles exceptions from AlpacaManager and provides
appropriate fallback behavior for the domain layer.
"""

from __future__ import annotations

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.errors.exceptions import DataProviderError, RateLimitError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.protocols.asset_metadata import AssetMetadataProvider
from the_alchemiser.shared.value_objects.symbol import Symbol

logger = get_logger(__name__)


class AlpacaAssetMetadataAdapter(AssetMetadataProvider):
    """Adapter implementing AssetMetadataProvider using AlpacaManager."""

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with AlpacaManager instance.

        Args:
            alpaca_manager: AlpacaManager instance for broker API access

        """
        self._alpaca_manager = alpaca_manager

    def is_fractionable(self, symbol: Symbol) -> bool:
        """Check if an asset supports fractional shares.

        Args:
            symbol: The symbol to check

        Returns:
            True if the asset supports fractional shares

        Raises:
            RateLimitError: If rate limit exceeded (should be retried)
            DataProviderError: If asset not found or data invalid

        """
        try:
            return self._alpaca_manager.is_fractionable(str(symbol))
        except RateLimitError:
            # Re-raise rate limit errors for upstream retry logic
            logger.warning("Rate limit checking fractionability", symbol=str(symbol))
            raise
        except DataProviderError:
            # Re-raise data provider errors (asset not found, etc.)
            logger.error("Asset not found for fractionability check", symbol=str(symbol))
            raise

    def get_asset_class(self, symbol: Symbol) -> str:
        """Get the asset class for a symbol.

        Args:
            symbol: The symbol to classify

        Returns:
            Asset class string (e.g., 'stock', 'etf', 'crypto')

        """
        asset_info = self._alpaca_manager.get_asset_info(str(symbol))
        if asset_info and asset_info.asset_class:
            return asset_info.asset_class
        return "unknown"

    def should_use_notional_order(self, symbol: Symbol, quantity: float) -> bool:
        """Determine if notional (dollar) orders should be used.

        Args:
            symbol: The symbol to trade
            quantity: Intended quantity

        Returns:
            True if notional orders should be used

        """
        try:
            # Use notional orders for non-fractionable assets
            if not self.is_fractionable(symbol):
                return True
        except (DataProviderError, RateLimitError) as e:
            # If we can't determine fractionability, use notional as safer fallback
            logger.warning(
                "Could not determine fractionability, using notional order",
                symbol=str(symbol),
                error=str(e),
            )
            return True

        # Use notional for very small fractional amounts (< 1 share)
        if quantity < 1.0:
            return True

        # Use notional if the fractional part is significant (> 0.1)
        return quantity % 1.0 > 0.1
