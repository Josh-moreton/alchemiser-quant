"""Business Unit: execution; Status: current.

Execution Validation Service.

Provides preflight validation for orders including fractionability checks
and quantity adjustments for non-fractionable assets.
"""

from __future__ import annotations

import logging
from decimal import ROUND_DOWN, Decimal

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO

logger = logging.getLogger(__name__)


class ExecutionValidationError(Exception):
    """Exception raised when execution validation fails."""

    def __init__(self, message: str, *, symbol: str, code: str | None = None) -> None:
        """Initialize with error details.

        Args:
            message: Error message
            symbol: Symbol that caused the error
            code: Optional error code (e.g., "40310000" for non-fractionable)

        """
        super().__init__(message)
        self.symbol = symbol
        self.code = code


class OrderValidationResult:
    """Result of order validation including any adjustments."""

    def __init__(
        self,
        *,
        is_valid: bool,
        adjusted_quantity: Decimal | None = None,
        warnings: list[str] | None = None,
        error_message: str | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize validation result.

        Args:
            is_valid: Whether order is valid and can proceed
            adjusted_quantity: Adjusted quantity if changes were made
            warnings: List of warnings about adjustments
            error_message: Error message if validation failed
            error_code: Error code if validation failed

        """
        self.is_valid = is_valid
        self.adjusted_quantity = adjusted_quantity
        self.warnings = warnings or []
        self.error_message = error_message
        self.error_code = error_code


class ExecutionValidator:
    """Validates orders before placement including fractionability checks."""

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with AlpacaManager for asset metadata.

        Args:
            alpaca_manager: AlpacaManager instance for asset info access

        """
        self.alpaca_manager = alpaca_manager

    def validate_order(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        *,
        correlation_id: str | None = None,
        auto_adjust: bool = True,
    ) -> OrderValidationResult:
        """Validate order before placement.

        Args:
            symbol: Asset symbol
            quantity: Order quantity
            side: "buy" or "sell"
            correlation_id: Optional correlation ID for tracing
            auto_adjust: Whether to auto-adjust non-fractionable quantities

        Returns:
            OrderValidationResult with validation outcome

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""

        # Get asset info
        asset_info = self.alpaca_manager.get_asset_info(symbol)
        if asset_info is None:
            logger.warning(f"{log_prefix} Could not get asset info for {symbol}, allowing order")
            return OrderValidationResult(is_valid=True)

        # Check if asset is tradable
        if not asset_info.tradable:
            return OrderValidationResult(
                is_valid=False,
                error_message=f"Asset {symbol} is not tradable",
                error_code="NOT_TRADABLE",
            )

        # Check fractionability
        if not asset_info.fractionable:
            return self._validate_non_fractionable_order(
                symbol,
                quantity,
                side,
                asset_info,
                correlation_id,
                auto_adjust=auto_adjust,
            )

        # Asset is fractionable, allow any positive quantity
        if quantity <= 0:
            return OrderValidationResult(
                is_valid=False,
                error_message=f"Invalid quantity {quantity} for {symbol}",
                error_code="INVALID_QUANTITY",
            )

        return OrderValidationResult(is_valid=True)

    def _validate_non_fractionable_order(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        asset_info: AssetInfoDTO,
        correlation_id: str | None,
        *,
        auto_adjust: bool,
    ) -> OrderValidationResult:
        """Validate order for non-fractionable asset.

        Args:
            symbol: Asset symbol
            quantity: Order quantity
            side: "buy" or "sell"
            asset_info: Asset information
            correlation_id: Optional correlation ID for tracing
            auto_adjust: Whether to auto-adjust quantities

        Returns:
            OrderValidationResult with validation outcome

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""

        # Check if quantity is already a whole number
        if quantity == quantity.to_integral_value():
            logger.debug(
                f"{log_prefix} Non-fractionable {symbol}: quantity {quantity} is already whole"
            )
            return OrderValidationResult(is_valid=True)

        # Quantity is fractional for non-fractionable asset
        if not auto_adjust:
            return OrderValidationResult(
                is_valid=False,
                error_message=f"Asset {symbol} is not fractionable but quantity {quantity} is fractional",
                error_code="40310000",  # Alpaca error code for non-fractionable
            )

        # Auto-adjust by rounding down to whole shares
        adjusted_quantity = quantity.quantize(Decimal("1"), rounding=ROUND_DOWN)

        # Check if rounding resulted in zero quantity
        if adjusted_quantity <= 0:
            logger.warning(
                f"{log_prefix} ❌ Non-fractionable {symbol}: quantity {quantity} rounds to zero, rejecting order"
            )
            return OrderValidationResult(
                is_valid=False,
                error_message=f"Non-fractionable asset {symbol} quantity {quantity} rounds to zero",
                error_code="ZERO_QUANTITY_AFTER_ROUNDING",
            )

        # Successfully adjusted
        warning_msg = (
            f"Non-fractionable {symbol}: adjusted quantity {quantity} → {adjusted_quantity} shares"
        )
        logger.info(f"{log_prefix} 🔄 {warning_msg}")

        return OrderValidationResult(
            is_valid=True,
            adjusted_quantity=adjusted_quantity,
            warnings=[warning_msg],
        )
