#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Asset Information Utilities.

Handles asset-specific information like fractionability, ETF types, and trading characteristics.
This helps optimize order placement strategies for different asset types.

This module now uses the AssetMetadataProvider protocol to avoid infrastructure dependencies.
"""

from __future__ import annotations

import math
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors.exceptions import DataProviderError
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from the_alchemiser.shared.protocols.asset_metadata import AssetMetadataProvider


class AssetType(Enum):
    """Asset type classification for trading optimization."""

    STOCK = "stock"
    ETF = "etf"
    ETN = "etn"
    LEVERAGED_ETF = "leveraged_etf"
    CRYPTO = "crypto"
    UNKNOWN = "unknown"


class FractionabilityDetector:
    """Detects and handles non-fractionable assets using AssetMetadataProvider.

    Professional trading systems need to handle assets that don't support
    fractional shares. This system delegates to an AssetMetadataProvider
    implementation for authoritative fractionability information.
    """

    def __init__(self, asset_metadata_provider: AssetMetadataProvider | None = None) -> None:
        """Initialize with optional AssetMetadataProvider.

        Args:
            asset_metadata_provider: Provider for asset metadata access

        """
        self.asset_metadata_provider = asset_metadata_provider
        self._fractionability_cache: dict[str, bool] = {}

        # Backup prediction patterns (used only when provider is unavailable)
        # Using frozenset for immutability
        self.backup_known_non_fractionable = frozenset({
            "FNGU",  # Confirmed non-fractionable via API
        })

    def _query_provider_fractionability(self, symbol: str) -> bool | None:
        """Query provider for definitive fractionability information.

        Args:
            symbol: Stock symbol to query

        Returns:
            True if fractionable, False if not, None if provider unavailable/error

        """
        if not self.asset_metadata_provider:
            return None

        try:
            from the_alchemiser.shared.value_objects.symbol import Symbol

            symbol_obj = Symbol(symbol)
            fractionable = self.asset_metadata_provider.is_fractionable(symbol_obj)
            logger.debug("Provider result", symbol=symbol, fractionable=fractionable)
            return fractionable

        except DataProviderError as e:
            # Provider unavailable, rate limited, or asset not found
            # Fall back to backup prediction
            logger.warning(
                "Provider error, using fallback",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None
        except Exception as e:
            # Catch any unexpected errors and fall back
            logger.warning(
                "Unexpected provider error, using fallback",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def is_fractionable(self, symbol: str, *, use_cache: bool = True) -> bool:
        """Determine if an asset supports fractional shares using provider.

        Args:
            symbol: Stock symbol to check
            use_cache: Whether to use cached results

        Returns:
            True if asset supports fractional shares, False otherwise

        """
        symbol = symbol.upper()

        # Check cache first
        if use_cache and symbol in self._fractionability_cache:
            cached_result = self._fractionability_cache[symbol]
            logger.debug("Cache hit", symbol=symbol, fractionable=cached_result)
            return cached_result

        # Query provider for authoritative answer
        provider_result = self._query_provider_fractionability(symbol)

        if provider_result is not None:
            # Cache the provider result
            self._fractionability_cache[symbol] = provider_result
            return provider_result

        # Fallback to backup prediction if provider unavailable
        logger.info("Using fallback prediction (provider unavailable)", symbol=symbol)
        fallback_result = self._fallback_fractionability_prediction(symbol)

        # Cache the fallback result with a warning
        self._fractionability_cache[symbol] = fallback_result
        return fallback_result

    def _fallback_fractionability_prediction(self, symbol: str) -> bool:
        """Fallback prediction when provider is unavailable.

        Args:
            symbol: Stock symbol to predict

        Returns:
            True if likely fractionable, False if likely not

        """
        symbol = symbol.upper()

        # Known non-fractionable from testing
        return symbol not in self.backup_known_non_fractionable

    def get_asset_type(self, symbol: str) -> AssetType:
        """Classify asset type for optimization strategies.

        Args:
            symbol: Stock symbol to classify

        Returns:
            AssetType enum value

        """
        symbol = symbol.upper()

        # Check if it's non-fractionable first
        if not self.is_fractionable(symbol):
            return AssetType.LEVERAGED_ETF  # Most non-fractionable assets are leveraged products

        # Regular ETFs (common patterns)
        if symbol in [
            "SPY",
            "QQQ",
            "IWM",
            "VTI",
            "VOO",
            "VEA",
            "BIL",
        ] or symbol.startswith(("VT", "VO")):
            return AssetType.ETF

        # Assume stocks by default
        return AssetType.STOCK

    def should_use_notional_order(self, symbol: str, quantity: Decimal | float) -> bool:
        """Determine if we should use notional (dollar) orders instead of quantity orders.

        Professional strategy using provider data:
        - Use notional orders for non-fractionable assets
        - Use notional orders for small fractional quantities
        - Use quantity orders for large whole-share quantities

        Args:
            symbol: Stock symbol
            quantity: Intended quantity to trade (Decimal preferred for precision)

        Returns:
            True if should use notional order, False for quantity order

        """
        # Convert to Decimal for precise comparisons
        if isinstance(quantity, float):
            quantity_dec = Decimal(str(quantity))
        else:
            quantity_dec = quantity

        # Always use notional for non-fractionable assets (provider-confirmed)
        if not self.is_fractionable(symbol):
            return True

        # Use notional for very small fractional amounts (< 1 share)
        if quantity_dec < Decimal("1.0"):
            return True

        # Use notional if the fractional part is significant (> 0.1)
        # Using explicit tolerance for float comparison
        fractional_part = quantity_dec % Decimal("1.0")
        return fractional_part > Decimal("0.1")

    def convert_to_whole_shares(
        self, symbol: str, quantity: Decimal | float, current_price: Decimal | float
    ) -> tuple[Decimal, bool]:
        """Convert fractional quantity to whole shares for non-fractionable assets.

        Uses provider data to determine if conversion is needed.

        Args:
            symbol: Stock symbol
            quantity: Fractional quantity desired (Decimal preferred for precision)
            current_price: Current price per share (Decimal preferred for precision)

        Returns:
            Tuple of (adjusted_quantity, used_rounding)

        """
        # Convert to Decimal for precise financial calculations
        if isinstance(quantity, float):
            quantity_dec = Decimal(str(quantity))
        else:
            quantity_dec = quantity

        if isinstance(current_price, float):
            price_dec = Decimal(str(current_price))
        else:
            price_dec = current_price

        # Only convert if asset is actually non-fractionable (provider-confirmed)
        if self.is_fractionable(symbol):
            return quantity_dec, False

        # Round down to whole shares for non-fractionable assets
        whole_shares = int(quantity_dec)
        whole_shares_dec = Decimal(whole_shares)
        
        # Check if rounding occurred using Decimal comparison
        used_rounding = not math.isclose(float(quantity_dec), float(whole_shares_dec), rel_tol=1e-9)

        if used_rounding:
            # Use Decimal arithmetic for precise money calculations
            original_value = quantity_dec * price_dec
            new_value = whole_shares_dec * price_dec
            
            logger.info(
                "Converting non-fractionable asset",
                symbol=symbol,
                original_quantity=str(quantity_dec),
                adjusted_quantity=whole_shares,
                original_value=str(original_value),
                new_value=str(new_value),
            )

        return whole_shares_dec, used_rounding

    def get_cache_stats(self) -> dict[str, int]:
        """Get statistics about the fractionability cache."""
        return {
            "cached_symbols": len(self._fractionability_cache),
            "fractionable_count": sum(1 for v in self._fractionability_cache.values() if v),
            "non_fractionable_count": sum(1 for v in self._fractionability_cache.values() if not v),
        }


# Global instance for easy access (will initialize with provider if available)
fractionability_detector = FractionabilityDetector()
