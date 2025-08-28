"""Business Unit: utilities; Status: current.

Infrastructure adapter implementing AssetMetadataProvider protocol.
"""

from __future__ import annotations

import logging

from the_alchemiser.domain.math.asset_info import FractionabilityDetector
from the_alchemiser.domain.math.protocols.asset_metadata_provider import AssetMetadataProvider
from the_alchemiser.domain.shared_kernel.value_objects.symbol import Symbol


class AlpacaAssetMetadataAdapter(AssetMetadataProvider):
    """Alpaca-based implementation of AssetMetadataProvider protocol."""

    def __init__(self, fractionability_detector: FractionabilityDetector | None = None) -> None:
        """Initialize with optional FractionabilityDetector.

        Args:
            fractionability_detector: Detector instance (will create global one if None)
        """
        if fractionability_detector is None:
            from the_alchemiser.domain.math.asset_info import fractionability_detector as global_detector
            fractionability_detector = global_detector
        
        self._detector = fractionability_detector
        self.logger = logging.getLogger(__name__)

    def is_fractionable(self, symbol: Symbol) -> bool:
        """Check if an asset supports fractional shares.

        Args:
            symbol: Symbol to check

        Returns:
            True if asset supports fractional shares
        """
        return self._detector.is_fractionable(symbol.as_str())

    def should_use_notional_order(self, symbol: Symbol, quantity: float) -> bool:
        """Determine if notional (dollar) orders should be used.

        Args:
            symbol: Symbol to check
            quantity: Intended quantity to trade

        Returns:
            True if should use notional order
        """
        return self._detector.should_use_notional_order(symbol.as_str(), quantity)

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
        return self._detector.convert_to_whole_shares(symbol.as_str(), quantity, current_price)